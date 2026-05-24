import { FormEvent, PointerEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AuthoringDiffSummary,
  AuthoringValidation,
  AuthoringFilePreviewResponse,
  AuthoringModLoadOrderResponse,
  AuthoringModSummary,
  AuthoringModValidation,
  AuthoringWorldSummary,
  AuthoringWorkflowPreset,
  AuthoringProjectSummary,
  ActionModDraft,
  ActionModPreviewResponse,
  ActionModTestRunResponse,
  DeclarativeActionDefinition,
  DeclarativeOutcome,
  ReferenceIndex,
  ReferenceIndexItem,
  ReferenceKind,
  LocalContentLibraryItem,
  LocalContentType,
  ArchiveImportResponse,
  balanceCheckItemEconomyAuthoring,
  DebugEvent,
  DebugNPCSimulationDetail,
  DebugNPCSimulationDryRunResponse,
  DebugNPCSimulationSummary,
  DebugPerformanceSample,
  ModuleActionDryRunResponse,
  ModuleDebugSummary,
  NPCBehaviorTimelineResponse,
  DebugPerformanceRecentResponse,
  DebugPerformanceSummaryResponse,
  applyScenarioTemplate,
  applyTemplateWizard,
  applyWorldPackWizard,
  applyBatchCharacterCardImportDraft,
  applyBatchLorebookClassificationDraft,
  applyNPCPackGenerator,
  applyQuestPackGenerator,
  applyLocationClusterTemplate,
  batchValidateLocalContentLibrary,
  applyNPCSimulationPresetDraft,
  applyRPScenarioTemplate,
  deleteSave,
  dryRunNPCSimulationTick,
  dryRunGameplayModuleAction,
  dryRunScriptPackageBuild,
  dryRunSaveTimelineReplay,
  buildScriptPackage,
  buildCampaignStarterKit,
  exportModArchive,
  exportBatchCharacterCardPack,
  exportCharacterPack,
  exportNPCPackGenerator,
  exportScriptPackage,
  exportCampaignStarterScriptPackage,
  exportSafeRPCharacterCard,
  exportSaveArchive,
  exportWorldArchive,
  exportLocalContentLibraryItem,
  importModArchive,
  importSaveArchive,
  importWorldArchive,
  importLocalContentLibraryArchive,
  applySaveMigration,
  dryRunSaveMigration,
  fetchAuthoringFile,
  fetchAuthoringFiles,
  fetchAuthoringMod,
  fetchAuthoringModLoadOrder,
  fetchAuthoringMods,
  fetchDialogueSceneAuthoring,
  fetchGroupRPSceneAuthoring,
  fetchNarrativeProjects,
  createNarrativeProject,
  validateNarrativeProject,
  fetchNarrativeProjectModes,
  fetchNovelManuscripts,
  createNovelManuscript,
  fetchNovelChapters,
  createNovelChapter,
  updateNovelChapter,
  fetchNovelScenes,
  createNovelScene,
  exportNovelManuscript,
  createNovelDraftSnapshot,
  fetchNovelDraftSnapshots,
  compareNovelDraftSnapshots,
  startNovelWritingSession,
  fetchCurrentNovelWritingSession,
  endNovelWritingSession,
  searchNovel,
  fetchNovelPreferences,
  saveNovelPreferences,
  fetchTavernCharacters,
  createTavernCharacter,
  importTavernCharacterCard,
  fetchTavernSessions,
  createTavernSession,
  fetchTavernMessages,
  sendTavernChatMessage,
  fetchTavernScenePresets,
  createTavernScenePreset,
  fetchMatureSettings,
  updateMatureSettings,
  fetchTavernMultiNPCScenes,
  createTavernMultiNPCScene,
  generateTavernMultiNPCReply,
  fetchTavernPreferences,
  saveTavernPreferences,
  fetchTavernRecoveryRecords,
  createTavernRecoveryRecord,
  previewTavernSessionExport,
  createTavernSessionExport,
  fetchRPSafetyDashboard,
  runRPSafetyDashboard,
  fetchWorldNpcSafeSummaries,
  adaptWorldNpcToTavern,
  createNovelToWorldDraft,
  validateNovelToWorldDraft,
  fetchNovelToWorldDrafts,
  previewWorldToNovel,
  fetchCrossModeTimeline,
  fetchCrossModeLinks,
  detectCrossModeConflicts,
  validateCrossMode,
  fetchCrossModeAudit,
  buildTavernApplyPlan,
  buildProjectModuleCompatibilityMatrix,
  certifyProjectModule,
  NovelManuscript,
  NovelChapter,
  NovelScene,
  NovelDraftSnapshot,
  WritingSessionState,
  NovelPreferences,
  NovelSearchResult,
  ModuleBrowserDetail,
  ModuleBrowserSummary,
  ModulePermissionSummary,
  AdvancedModuleDashboardItem,
  AdvancedModuleDraftValidation,
  ModAuditRecord,
  ModCompatibilityMatrix,
  ModQualityGateResult,
  fetchProjectModule,
  fetchProjectModuleAudit,
  fetchProjectModuleCompatibility,
  fetchProjectModulePermissions,
  fetchProjectModulePermissionsSummary,
  fetchProjectModules,
  fetchAuthoringModuleDashboard,
  fetchEconomySimConfig,
  fetchFactionWarConfig,
  fetchTacticalCombatConfig,
  runProjectAdvancedModuleQualityGate,
  runProjectModuleQualityGate,
  scanProjectModules,
  validateEconomySimDraft,
  validateFactionWarDraft,
  validateProjectModule,
  validateTacticalCombatDraft,
  fetchAuthoringMap,
  fetchItemEconomyAuthoring,
  fetchNPCGoalGraph,
  fetchRumorCrimeAuthoring,
  fetchRPCharacterAuthoring,
  fetchSocialAuthoringGraph,
  fetchValidationGraph,
  generateQuestGraphScenarioDraft,
  fetchAuthoringWorld,
  fetchAuthoringWorlds,
  fetchAuthoringWorkflowPresets,
  fetchAuthoringProjectSummary,
  previewActionModDraft,
  validateActionModDraft,
  exportActionModDraft,
  runActionModDraftTests,
  fetchImportExportProfiles,
  fetchProductionPipelineSummary,
  fetchModelCompatibilityMatrix,
  fetchModelUsageSummary,
  fetchProjectProviderUsageByMode,
  fetchProjectProviderUsageByProvider,
  fetchProjectProviderCapabilityMatrix,
  fetchProjectProviderModelAssignments,
  fetchProjectProviders,
  createProjectProvider,
  saveProjectProviderModelAssignments,
  validateProjectProvider,
  validateProjectProviderModelAssignments,
  fetchProjectProviderStatus,
  fetchProjectProviderUsageRecent,
  fetchProjectProviderUsageSummary,
  fetchProviderCapabilities,
  fetchTokenBudgetProfiles,
  fetchRecentModelUsage,
  fetchProviderRoutingSummary,
  fetchStudioWorkspaces,
  fetchWorkspaceTemplates,
  addStudioWorkspace,
  createWorkspaceFromTemplate,
  selectStudioWorkspace,
  fetchRecentProjects,
  removeRecentProject,
  clearRecentProjects,
  createDiagnosticsBundle,
  fetchReferenceIndex,
  fetchLocalContentLibrary,
  searchLocalContentLibrary,
  fetchLocationClusterTemplates,
  fetchWorldBranches,
  fetchScenarioTemplates,
  fetchRPScenarioTemplates,
  fetchScenarioRegression,
  fetchScenarioRegressionCases,
  fetchAuthoringScenarios,
  fetchGameState,
  fetchDebugFactionGraph,
  fetchDebugRelationshipGraph,
  fetchPlayerFactionGraph,
  fetchPlayerRelationshipGraph,
  fetchQuestGraph,
  fetchNarrativeEval,
  fetchNarrativeEvalRecent,
  fetchDebugPerformanceRecent,
  fetchDebugPerformanceSummary,
  fetchNPCSimulationDebug,
  fetchNPCSimulationDebugDetail,
  fetchNPCSimulationDebugTicks,
  fetchGameplayModuleDebug,
  fetchGameplayModuleDebugDetail,
  fetchNPCBehaviorTimeline,
  fetchNPCSimulationPresets,
  fetchPlaytest,
  fetchPlaytestRecent,
  fetchSaveDebugEvents,
  fetchSaveTimelineReplay,
  fetchSaveMigrationStatus,
  fetchSessionDebugEvents,
  fetchSessionTimelineReplay,
  fetchStudioConfigSummary,
  fetchLocalConfigSummary,
  fetchLocalConfigIssues,
  generateLocalEnvTemplate,
  fetchLocalUpdateNotes,
  fetchDesktopHealth,
  runDesktopHealthCheck,
  fetchLocalStudioStatus,
  fetchLocalStudioConfigSummary,
  fetchLocalStudioStartupChecks,
  createBackupDryRun,
  createLocalBackup,
  restoreBackupDryRun,
  fetchRecoveryIssues,
  buildRecoveryPlan,
  dryRunRecovery,
  fetchLocalLogs,
  previewDiagnosticsBundle,
  fetchCrashReports,
  fetchCrashReport,
  deleteCrashReport,
  fetchStudioStatus,
  fetchContentCoverage,
  reviewContentDiff,
  GameInputResponse,
  ContentDiffReview,
  ContentCoveragePlan,
  GraphResponse,
  listSaves,
  loadGame,
  NarrativeEvalReport,
  NarratorStyleReport,
  NPCVoiceStyleReport,
  ContextInspectType,
  ContextSnapshot,
  ModelCompatibilityMatrix,
  ModelUsageRecord,
  ModelUsageSummary,
  CostLatencyGroupSummary,
  DiagnosticsBundleCreateResponse,
  ProviderProfileDraft,
  ProviderProfileSummary,
  ModelCapabilityMatrixRow,
  ProviderModelCapabilityMatrix,
  ProviderBenchmarkReport,
  ProviderCapabilityCatalog,
  BudgetReport,
  TokenBudgetProfile,
  TokenBudgetUseCase,
  ProviderRoutingPreview,
  ProjectProviderModelAssignmentSummary,
  ProviderRoutingRule,
  ProviderRoutingSummary,
  ProviderRoutingUseCase,
  ProjectWorkspace,
  WorkspaceTemplate,
  WorkspaceTemplateType,
  RecentProjectEntry,
  PromptDiffReport,
  PromptRegressionReport,
  PlaytestReport,
  PlaytestActionRecord,
  PlaytestBatchRun,
  PromptABTestReport,
  PromptABUseCase,
  previewAuthoringFileChange,
  previewAuthoringMap,
  previewAuthoringScenario,
  previewQuestGraph,
  previewScenarioTemplate,
  previewTemplateWizard,
  previewWorldPackWizard,
  previewNPCPackGenerator,
  previewBatchCharacterCardImport,
  previewBatchLorebookClassification,
  previewCampaignStarterKit,
  previewQuestPackGenerator,
  previewLocationClusterTemplate,
  previewWorldMerge,
  previewRPScenarioTemplate,
  planContentCoverage,
  runNarrativeEval,
  runContentCoverage,
  runPlaytest,
  runPlaytestBatch,
  runPromptABTest,
  runProviderBenchmark,
  runNarratorStyleExperiment,
  runNPCVoiceStyleExperiment,
  runStructuredOutputReliability,
  runPromptRegressionSuite,
  runLocalModelDiagnostics,
  recomputeModelCompatibilityMatrix,
  estimateTokenBudget,
  previewProviderRoutingRule,
  saveProviderRoutingConfig,
  reviewPromptDiff,
  StructuredOutputReliabilityReport,
  LocalModelDiagnosticReport,
  inspectPromptLabContext,
  runScenarioRegression,
  saveGame,
  saveAuthoringFile,
  saveAuthoringMap,
  saveAuthoringScenario,
  saveQuestGraph,
  SaveSummary,
  SaveMigrationResponse,
  SaveMigrationStatus,
  ScenarioTemplate,
  ScenarioTemplatePreviewResponse,
  MergeResolution,
  TemplateWizardDraft,
  TemplateWizardPreviewResponse,
  TemplateWizardType,
  WorldPackWizardDraft,
  WorldPackWizardPreviewResponse,
  NPCPackGeneratorDraft,
  NPCPackGeneratorPreviewResponse,
  QuestPackGeneratorDraft,
  QuestPackGeneratorPreviewResponse,
  LocationClusterTemplate,
  LocationClusterPreviewResponse,
  WorldBranch,
  WorldMergeDraft,
  RPScenarioTemplate,
  RPScenarioTemplatePreviewResponse,
  ScenarioAuthoringPreviewResponse,
  ScenarioRegressionCase,
  ScenarioRegressionRun,
  QuestGraphResponse,
  QuestStageNode,
  QuestTriggerNode,
  startGame,
  StudioConfigSummary,
  LocalConfigIssue,
  LocalConfigSummary,
  LocalEnvTemplateResponse,
  LocalUpdateNotesIndex,
  DesktopHealthCheckReport,
  LocalStudioStatus,
  LocalStudioConfigSummary,
  LocalStudioStartupChecks,
  BackupPlan,
  BackupCreateResponse,
  RestorePlan,
  RecoveryIssue,
  RecoveryPlan,
  LocalLogListResponse,
  DiagnosticsBundlePreview,
  CrashReport,
  StudioStatus,
  submitPlayerInput,
  TimelineReplayResponse,
  TimelineEventView,
  validateAuthoringMap,
  validateAuthoringScenario,
  validateQuestGraph,
  validateAuthoringWorld,
  validateAuthoringMod,
  VisibleState,
  ValidationGraph,
  MapVisualEdge,
  MapVisualEdgeType,
  MapVisualGraph,
  MapVisualNode,
  MapVisibility,
  NPCGoalAuthoringGraph,
  NPCGoalAuthoringNode,
  NPCGoalNode,
  NPCSimulationPreset,
  ItemEconomyAuthoring,
  ItemEconomyItem,
  ExportProfile,
  ImportProfile,
  MerchantEconomyNode,
  ShopInventoryEdge,
  CharacterCardImportReport,
  BatchCharacterCardImportReport,
  BatchLorebookClassificationReport,
  ScriptPackageBuildReport,
  ScriptPackageBuildRequest,
  CampaignStarterKitDraft,
  CampaignStarterKitPreview,
  ProductionPipelineSummary,
  ProductionPipelineTask,
  RumorAuthoringNode,
  RumorCrimeConsequenceAuthoring,
  RPCharacterAuthoring,
  RPCharacterAuthoringProfile,
  DialogueSceneAuthoring,
  DialogueSceneTemplate,
  GroupRPSceneAuthoring,
  GroupRPSceneTemplate,
  getErrorMessageSafe,
  NarrativeProjectSummary,
  NarrativeProjectModeStatus,
  TavernCharacter,
  TavernSession,
  TavernMessage,
  TavernScenePreset,
  TavernPreferences,
  TavernSessionRecoveryRecord,
  TavernSessionExportPreview,
  RPSafetyDashboardReport,
  WorldNpcSafeSummary,
  MatureSettingsResponse,
  MultiNPCSceneSummary,
  CrossModeDraftSummary,
  CrossModeTimelineEntry,
  CrossModeLinkReviewReport,
  CrossModeConflictReport,
  CrossModeAuditRecord,
  ExampleDialogue,
  fetchExampleDialogues,
  previewNPCGoalGraph,
  previewNPCSimulationPreset,
  previewItemEconomyAuthoring,
  previewExampleDialogues,
  previewRPCharacterAuthoring,
  previewRPCharacterImport,
  previewDialogueSceneAuthoring,
  previewGroupRPSceneAuthoring,
  previewRumorCrimeAuthoring,
  previewSocialAuthoringGraph,
  saveNPCGoalGraph,
  saveItemEconomyAuthoring,
  saveExampleDialogues,
  saveRPCharacterAuthoring,
  saveDialogueSceneAuthoring,
  saveGroupRPSceneAuthoring,
  saveRumorCrimeAuthoring,
  saveSocialAuthoringGraph,
  saveWorldMerge,
  selectPromptProfile,
  SocialAuthoringGraph,
  validateItemEconomyAuthoring,
  validateRPCharacterAuthoring,
  validateDialogueSceneAuthoring,
  validateGroupRPSceneAuthoring,
  validateNPCGoalGraph,
  validateExampleDialogues,
  validateRumorCrimeAuthoring,
  validateSocialAuthoringGraph,
  validateTemplateWizard,
  validateWorldPackWizard,
  validateNPCPackGenerator,
  validateQuestPackGenerator,
  validateScriptPackage,
  validateLocalContentLibraryItem,
  fetchWorldHealth,
  runWorldHealth,
  continueDialogue,
  ContentCoverageReport,
  DialogueModeResponse,
  endDialogue,
  endGroupDialogue,
  GroupDialogueSceneResponse,
  selectGroupDialogueNextSpeaker,
  WorldHealthScore,
  startGroupDialogue,
  startDialogue
} from "./api";
import {
  CharacterArcPanel,
  ChapterCard,
  ChapterEditorPro,
  DraftSaveStatus,
  DraftVersionPanel,
  LinkedRefList,
  ManuscriptCard,
  ManuscriptDashboard,
  NovelExportWizard,
  NovelPromptProviderPanel,
  NovelQualityDashboard,
  NovelSafeSummaryPanel,
  NovelSearchFilterBar,
  NovelToolbar,
  NovelWorkspaceShell,
  OutlineNodeView,
  OutlineTreePro,
  PlotForeshadowingBoard,
  SceneCardsBoard,
  TimelineLinkPanel,
  WorldToNovelImportPanel,
  WordCountBadge,
  WorldBibleSidebar,
  WritingSessionDashboard,
  buildNovelQualityIssues
} from "./novelUi";
import {
  BoundaryMatureSettingsPanel,
  CharacterCardLibrary,
  CharacterVoiceLabPanel,
  ChatSaveStatus,
  EmotionArcPanel,
  MultiNPCScenePro,
  RelationshipTonePanel,
  RPMemoryPanel,
  RPSafetyDashboardPanel,
  SceneMoodPresetPanel,
  SingleCharacterChatPro,
  TavernCharacterEditor,
  TavernCrossModeSafetyPanel,
  TavernPromptProviderPanel,
  TavernSafeSummaryPanel,
  TavernSessionCard,
  TavernToolbar,
  TavernWorkspaceShell
} from "./tavernUi";
import {
  DebugGate,
  DeductionBoardPanel,
  EconomyDashboardPanel,
  FactionWarDashboardPanel,
  InventoryTradePanel,
  LocationCard,
  ModuleStatusBadge,
  NPCRelationshipPanel,
  QuestJournalPanel,
  SurvivalTravelPanel,
  TacticalCombatPanel,
  VisibleStateInspector,
  WorldActionCategory,
  WorldActionInputPanel,
  WorldAdvancedModulePanels,
  WorldPromptProviderPanel,
  WorldQualityPlaytestPanel,
  WorldSaveLoadPanel,
  WorldPlayMainView,
  WorldTimelineEventLogPanel,
  WorldWorkspaceNavigation,
  WorldWorkspaceShell
} from "./worldUi";

type StoryEntry = {
  id: number;
  text: string;
};

const WORLD_OPTIONS = [{ id: "mist_valley", name: "Mist Valley" }];
const AUTHORING_FILES = [
  "manifest.yaml",
  "locations.yaml",
  "npcs.yaml",
  "items.yaml",
  "quests.yaml",
  "facts.yaml",
  "factions.yaml",
  "rumors.yaml",
  "relationships.yaml",
  "example_dialogues.yaml"
];

const AUTHORING_FILE_GROUPS = [
  {
    title: "Core",
    files: ["manifest.yaml", "locations.yaml", "npcs.yaml", "items.yaml", "quests.yaml", "facts.yaml"]
  },
  {
    title: "Social",
    files: ["factions.yaml", "rumors.yaml", "relationships.yaml"]
  },
  {
    title: "Roleplay",
    files: ["npcs.yaml", "example_dialogues.yaml"]
  },
  {
    title: "Economy / Mods",
    files: ["items.yaml", "npcs.yaml", "mod.yaml", "manifest.yaml"]
  }
];

const FORM_SUPPORTED_FILES = new Set([
  "locations.yaml",
  "npcs.yaml",
  "items.yaml",
  "facts.yaml",
  "quests.yaml"
]);

const ROOT_KEYS: Record<string, string> = {
  "locations.yaml": "locations",
  "npcs.yaml": "npcs",
  "items.yaml": "items",
  "facts.yaml": "facts",
  "quests.yaml": "quests",
  "factions.yaml": "factions",
  "rumors.yaml": "rumors",
  "relationships.yaml": "relationships",
  "example_dialogues.yaml": "example_dialogues"
};

const MAP_EDGE_TYPES: MapVisualEdgeType[] = ["exit", "one_way", "locked", "hidden", "conditional"];
const MAP_VISIBILITIES: MapVisibility[] = ["public", "hidden", "discoverable"];
const TIMELINE_FILTERS = ["all", "player", "system", "npc", "quest", "combat", "social", "migration"] as const;
type TimelineFilter = (typeof TIMELINE_FILTERS)[number];
type AuthoringToolId =
  | "project_dashboard"
  | "map"
  | "quests"
  | "npc_goals"
  | "social"
  | "economy"
  | "rumor_crime"
  | "rp_characters"
  | "dialogue_scenes"
  | "group_rp_scenes"
  | "example_dialogue"
  | "scenarios"
  | "templates"
  | "template_wizard"
  | "world_pack_wizard"
  | "npc_pack_generator"
  | "quest_pack_generator"
  | "location_clusters"
  | "action_mods"
  | "advanced_modules"
  | "merge_assistant"
  | "diff_review"
  | "library"
  | "validation";

const AUTHORING_TOOL_NAV: { id: AuthoringToolId; label: string; description: string; preferredFile?: string }[] = [
  { id: "project_dashboard", label: "Project", description: "status, quality, recent edits" },
  { id: "map", label: "Map", description: "locations, exits, visual coordinates", preferredFile: "locations.yaml" },
  { id: "quests", label: "Quests", description: "quest stages, triggers, rewards", preferredFile: "quests.yaml" },
  { id: "npc_goals", label: "NPC Goals", description: "goal priorities and planning constraints", preferredFile: "npcs.yaml" },
  { id: "social", label: "Factions / Relationships", description: "factions, trust, conflict, visibility", preferredFile: "factions.yaml" },
  { id: "economy", label: "Items / Economy", description: "items, prices, merchants, shops", preferredFile: "items.yaml" },
  { id: "rumor_crime", label: "Rumors / Crime", description: "rumors and social consequence chains", preferredFile: "rumors.yaml" },
  { id: "rp_characters", label: "RP Characters", description: "profiles, voice, emotions, safe imports", preferredFile: "npcs.yaml" },
  { id: "dialogue_scenes", label: "Dialogue Scenes", description: "participants, topics, moods, openings", preferredFile: "dialogue_scenes.yaml" },
  { id: "group_rp_scenes", label: "Group RP Scenes", description: "multi-NPC scenes, roles, tension", preferredFile: "group_rp_scenes.yaml" },
  { id: "example_dialogue", label: "Example Dialogue", description: "style-only dialogue samples", preferredFile: "example_dialogues.yaml" },
  { id: "scenarios", label: "Scenarios", description: "regression case authoring" },
  { id: "templates", label: "Templates", description: "local scenario templates" },
  { id: "template_wizard", label: "Template Wizard", description: "guided template drafts" },
  { id: "world_pack_wizard", label: "World Pack Wizard", description: "new world pack drafts" },
  { id: "npc_pack_generator", label: "NPC Pack", description: "batch NPC draft generation" },
  { id: "quest_pack_generator", label: "Quest Pack", description: "batch questline drafts" },
  { id: "location_clusters", label: "Location Clusters", description: "map cluster templates" },
  { id: "action_mods", label: "Action Mods", description: "declarative action editor" },
  { id: "advanced_modules", label: "Advanced Modules", description: "combat, economy, faction war, magic, hacking, crafting" },
  { id: "merge_assistant", label: "Merge Assistant", description: "branch conflict review" },
  { id: "diff_review", label: "Diff Review", description: "content change review" },
  { id: "library", label: "Library", description: "local content packages" },
  { id: "validation", label: "Validation", description: "validation graph and issue routing" }
];

const DANGEROUS_ACTION_COPY = {
  overwriteWorldFile: "Overwrite a local world-pack file after preview and validation? Active sessions are not changed.",
  saveGraphChanges: "Save graph changes to local YAML after validation? Active GameState is not changed.",
  applyMigration: "Apply migration to this save? Dry-run first is recommended. The backend keeps migration history/backup metadata.",
  importPackageApply: "Apply this local package import after backend validation? Existing content is not overwritten unless overwrite is enabled.",
  deleteSave: "Delete this local save? This cannot be undone from the Studio UI."
};

const FORM_FIELDS: Record<string, AuthoringFormField[]> = {
  "locations.yaml": [
    { name: "id", label: "Id", kind: "text" },
    { name: "name", label: "Name", kind: "text" },
    { name: "description", label: "Description", kind: "textarea" }
  ],
  "npcs.yaml": [
    { name: "id", label: "Id", kind: "text" },
    { name: "name", label: "Name", kind: "text" },
    { name: "location_id", label: "Location", kind: "text" },
    { name: "faction_id", label: "Faction", kind: "text" },
    { name: "personality", label: "Personality", kind: "textarea" }
  ],
  "items.yaml": [
    { name: "id", label: "Id", kind: "text" },
    { name: "name", label: "Name", kind: "text" },
    { name: "description", label: "Description", kind: "textarea" },
    { name: "location_id", label: "Location", kind: "text" },
    { name: "portable", label: "Portable", kind: "boolean" },
    { name: "hidden", label: "Hidden", kind: "boolean" },
    { name: "discoverable", label: "Discoverable", kind: "boolean" },
    { name: "base_price", label: "Base price", kind: "number" },
    { name: "tradeable", label: "Tradeable", kind: "boolean" }
  ],
  "facts.yaml": [
    { name: "id", label: "Id", kind: "text" },
    { name: "text", label: "Text", kind: "textarea" },
    { name: "visibility", label: "Visibility", kind: "select", options: ["public", "hidden", "discoverable"] }
  ],
  "quests.yaml": [
    { name: "id", label: "Id", kind: "text" },
    { name: "title", label: "Title", kind: "text" },
    { name: "description", label: "Description", kind: "textarea" },
    { name: "initial_stage", label: "Initial stage", kind: "text" },
    { name: "visibility", label: "Visibility", kind: "select", options: ["public", "hidden"] }
  ]
};

type AuthoringViewMode = "raw" | "form";
type AuthoringFormField = {
  name: string;
  label: string;
  kind: "text" | "textarea" | "boolean" | "number" | "select";
  options?: string[];
};
type ParsedAuthoringEntity = {
  id: string;
  startLine: number;
  endLine: number;
  fields: Record<string, string>;
};

const SCENE_MOOD_PRESETS = [
  { id: "", label: "Default" },
  { id: "mist_tension", label: "Mist tension" },
  { id: "quiet_warmth", label: "Quiet warmth" },
  { id: "solemn_wuxia", label: "Solemn wuxia" }
];

const DIALOGUE_MODES = ["focused", "casual", "interrogation", "negotiation", "intimate", "conflict"];
type AppMode = "project" | "studio" | "play" | "authoring" | "prompt_lab";
const FIRST_RUN_ONBOARDING_KEY = "ai-narrative-studio:first-run-onboarding:v3";

function firstRunOnboardingDismissed(): boolean {
  try {
    return window.localStorage.getItem(FIRST_RUN_ONBOARDING_KEY) === "completed";
  } catch {
    return false;
  }
}

export function App() {
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedWorldId, setSelectedWorldId] = useState<string>("mist_valley");
  const [visibleState, setVisibleState] = useState<VisibleState | null>(null);
  const [turn, setTurn] = useState<number>(0);
  const [story, setStory] = useState<StoryEntry[]>([]);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const [dialogue, setDialogue] = useState<DialogueModeResponse | null>(null);
  const [groupScene, setGroupScene] = useState<GroupDialogueSceneResponse | null>(null);
  const [sceneMoodPresetId, setSceneMoodPresetId] = useState<string>("");
  const [selectedDialogueMode, setSelectedDialogueMode] = useState<string>("focused");
  const [input, setInput] = useState<string>("");
  const [recentWorldActions, setRecentWorldActions] = useState<string[]>([]);
  const [worldActionCategory, setWorldActionCategory] = useState<WorldActionCategory>("all");
  const [debugOpen, setDebugOpen] = useState<boolean>(true);
  const [lastResponse, setLastResponse] = useState<unknown>(null);
  const [timeline, setTimeline] = useState<DebugEvent[]>([]);
  const [timelineError, setTimelineError] = useState<string>("");
  const [timelineReplay, setTimelineReplay] = useState<TimelineReplayResponse | null>(null);
  const [timelineReplayError, setTimelineReplayError] = useState<string>("");
  const [timelineReplaySource, setTimelineReplaySource] = useState<"session" | "save">("session");
  const [timelineReplayFilter, setTimelineReplayFilter] = useState<TimelineFilter>("all");
  const [timelineReplayDryRun, setTimelineReplayDryRun] = useState<TimelineReplayResponse | null>(null);
  const [timelineReplayDryRunError, setTimelineReplayDryRunError] = useState<string>("");
  const [playerRelationshipGraph, setPlayerRelationshipGraph] = useState<GraphResponse | null>(null);
  const [playerFactionGraph, setPlayerFactionGraph] = useState<GraphResponse | null>(null);
  const [debugRelationshipGraph, setDebugRelationshipGraph] = useState<GraphResponse | null>(null);
  const [debugFactionGraph, setDebugFactionGraph] = useState<GraphResponse | null>(null);
  const [graphError, setGraphError] = useState<string>("");
  const [debugGraphError, setDebugGraphError] = useState<string>("");
  const [npcSimulationSummaries, setNPCSimulationSummaries] = useState<DebugNPCSimulationSummary[]>([]);
  const [selectedSimulationNPCId, setSelectedSimulationNPCId] = useState<string>("");
  const [npcSimulationDetail, setNPCSimulationDetail] = useState<DebugNPCSimulationDetail | null>(null);
  const [npcSimulationEvents, setNPCSimulationEvents] = useState<DebugEvent[]>([]);
  const [npcSimulationDryRun, setNPCSimulationDryRun] = useState<DebugNPCSimulationDryRunResponse | null>(null);
  const [npcSimulationError, setNPCSimulationError] = useState<string>("");
  const [npcBehaviorTimeline, setNPCBehaviorTimeline] = useState<NPCBehaviorTimelineResponse | null>(null);
  const [npcBehaviorTimelineError, setNPCBehaviorTimelineError] = useState<string>("");
  const [npcBehaviorTurnFrom, setNPCBehaviorTurnFrom] = useState<string>("");
  const [npcBehaviorTurnTo, setNPCBehaviorTurnTo] = useState<string>("");
  const [npcBehaviorFilter, setNPCBehaviorFilter] = useState<string>("all");
  const [moduleDebugSummaries, setModuleDebugSummaries] = useState<ModuleDebugSummary[]>([]);
  const [selectedModuleDebugId, setSelectedModuleDebugId] = useState<string>("");
  const [moduleDebugDetail, setModuleDebugDetail] = useState<ModuleDebugSummary | null>(null);
  const [moduleDebugDryRun, setModuleDebugDryRun] = useState<ModuleActionDryRunResponse | null>(null);
  const [moduleDebugError, setModuleDebugError] = useState<string>("");
  const [crashReports, setCrashReports] = useState<CrashReport[]>([]);
  const [selectedCrashReportId, setSelectedCrashReportId] = useState<string>("");
  const [selectedCrashReport, setSelectedCrashReport] = useState<CrashReport | null>(null);
  const [crashReportError, setCrashReportError] = useState<string>("");
  const [saves, setSaves] = useState<SaveSummary[]>([]);
  const [selectedSaveId, setSelectedSaveId] = useState<string>("");
  const [migrationStatusBySaveId, setMigrationStatusBySaveId] = useState<Record<string, SaveMigrationStatus>>({});
  const [migrationResultBySaveId, setMigrationResultBySaveId] = useState<Record<string, SaveMigrationResponse>>({});
  const [migrationError, setMigrationError] = useState<string>("");
  const [saveWorldFilter, setSaveWorldFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [mode, setMode] = useState<AppMode>("studio");
  const [requestedAuthoringTool, setRequestedAuthoringTool] = useState<AuthoringToolId | null>(null);
  const [studioStatus, setStudioStatus] = useState<StudioStatus | null>(null);
  const [studioStatusError, setStudioStatusError] = useState<string>("");
  const [studioConfigSummary, setStudioConfigSummary] = useState<StudioConfigSummary | null>(null);
  const [localConfigSummary, setLocalConfigSummary] = useState<LocalConfigSummary | null>(null);
  const [localConfigIssues, setLocalConfigIssues] = useState<LocalConfigIssue[]>([]);
  const [localEnvTemplate, setLocalEnvTemplate] = useState<LocalEnvTemplateResponse | null>(null);
  const [localUpdateNotes, setLocalUpdateNotes] = useState<LocalUpdateNotesIndex | null>(null);
  const [localUpdateNotesError, setLocalUpdateNotesError] = useState<string>("");
  const [desktopHealth, setDesktopHealth] = useState<DesktopHealthCheckReport | null>(null);
  const [desktopHealthError, setDesktopHealthError] = useState<string>("");
  const [localStudioStatus, setLocalStudioStatus] = useState<LocalStudioStatus | null>(null);
  const [localStudioConfig, setLocalStudioConfig] = useState<LocalStudioConfigSummary | null>(null);
  const [localStudioStartupChecks, setLocalStudioStartupChecks] = useState<LocalStudioStartupChecks | null>(null);
  const [localStudioError, setLocalStudioError] = useState<string>("");
  const [backupPlan, setBackupPlan] = useState<BackupPlan | null>(null);
  const [backupResult, setBackupResult] = useState<BackupCreateResponse | null>(null);
  const [restorePlan, setRestorePlan] = useState<RestorePlan | null>(null);
  const [backupRestoreError, setBackupRestoreError] = useState<string>("");
  const [recoveryIssues, setRecoveryIssues] = useState<RecoveryIssue[]>([]);
  const [recoveryPlan, setRecoveryPlan] = useState<RecoveryPlan | null>(null);
  const [recoveryError, setRecoveryError] = useState<string>("");
  const [localLogs, setLocalLogs] = useState<LocalLogListResponse | null>(null);
  const [localLogsError, setLocalLogsError] = useState<string>("");
  const [diagnosticsBundlePreview, setDiagnosticsBundlePreview] = useState<DiagnosticsBundlePreview | null>(null);
  const [diagnosticsBundleCreateResult, setDiagnosticsBundleCreateResult] = useState<DiagnosticsBundleCreateResponse | null>(null);
  const [diagnosticsBundleError, setDiagnosticsBundleError] = useState<string>("");
  const [firstRunDismissed, setFirstRunDismissed] = useState<boolean>(() => firstRunOnboardingDismissed());
  const [studioConfigError, setStudioConfigError] = useState<string>("");
  const [projectWorkspaces, setProjectWorkspaces] = useState<ProjectWorkspace[]>([]);
  const [workspaceTemplates, setWorkspaceTemplates] = useState<WorkspaceTemplate[]>([]);
  const [recentProjects, setRecentProjects] = useState<RecentProjectEntry[]>([]);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState<string>("");
  const [workspaceError, setWorkspaceError] = useState<string>("");
  const [workspaceMessage, setWorkspaceMessage] = useState<string>("");
  const [narrativeProjects, setNarrativeProjects] = useState<NarrativeProjectSummary[]>([]);
  const [currentNarrativeProjectId, setCurrentNarrativeProjectId] = useState<string>("");
  const [projectModeStatuses, setProjectModeStatuses] = useState<NarrativeProjectModeStatus[]>([]);
  const [projectShellError, setProjectShellError] = useState<string>("");
  const [projectShellMessage, setProjectShellMessage] = useState<string>("");
  const [narrativeEvalReports, setNarrativeEvalReports] = useState<NarrativeEvalReport[]>([]);
  const [selectedNarrativeEval, setSelectedNarrativeEval] = useState<NarrativeEvalReport | null>(null);
  const [narrativeEvalError, setNarrativeEvalError] = useState<string>("");
  const [performanceRecent, setPerformanceRecent] = useState<DebugPerformanceRecentResponse | null>(null);
  const [performanceSummary, setPerformanceSummary] = useState<DebugPerformanceSummaryResponse | null>(null);
  const [performanceError, setPerformanceError] = useState<string>("");
  const [playtestReports, setPlaytestReports] = useState<PlaytestReport[]>([]);
  const [selectedPlaytest, setSelectedPlaytest] = useState<PlaytestReport | null>(null);
  const [playtestBatchReport, setPlaytestBatchReport] = useState<PlaytestBatchRun | null>(null);
  const [playtestError, setPlaytestError] = useState<string>("");
  const [scenarioRegressionCases, setScenarioRegressionCases] = useState<ScenarioRegressionCase[]>([]);
  const [scenarioRegressionRuns, setScenarioRegressionRuns] = useState<ScenarioRegressionRun[]>([]);
  const [selectedScenarioRegressionRun, setSelectedScenarioRegressionRun] = useState<ScenarioRegressionRun | null>(null);
  const [scenarioRegressionError, setScenarioRegressionError] = useState<string>("");
  const [worldHealth, setWorldHealth] = useState<WorldHealthScore | null>(null);
  const [worldHealthError, setWorldHealthError] = useState<string>("");
  const [contentCoverage, setContentCoverage] = useState<ContentCoverageReport | null>(null);
  const [contentCoverageError, setContentCoverageError] = useState<string>("");

  useEffect(() => {
    void handleStart();
    void refreshSaves();
    void refreshStudioStatus();
    void refreshStudioConfigSummary();
    void refreshLocalConfig();
    void refreshLocalUpdateNotes();
    void refreshDesktopHealth();
    void refreshLocalStudioUX();
    void refreshRecovery();
    void refreshLocalLogs();
    void refreshDiagnosticsBundlePreview();
    void refreshProjectWorkspaces();
    void refreshNarrativeProjects();
    void refreshWorkspaceTemplates();
    void refreshRecentProjects();
    void refreshNarrativeEvals();
    void refreshPerformance();
    void refreshPlaytests();
    void refreshScenarioRegressions();
    void refreshWorldHealth();
    void refreshContentCoverage();
  }, []);

  const knownFacts = useMemo(
    () => visibleState?.known_facts ?? [],
    [visibleState?.known_facts]
  );
  const socialDebugEvents = useMemo(
    () => timeline.filter((event) => isSocialDebugEvent(event)),
    [timeline]
  );
  const combatDebugEvents = useMemo(
    () => timeline.filter((event) => isCombatDebugEvent(event)),
    [timeline]
  );
  const rawReputationDeltas = useMemo(
    () =>
      timeline.flatMap((event) =>
        event.state_deltas
          .filter((delta) => delta.path.startsWith("factions."))
          .map((delta) => ({
            event_id: event.event_id,
            turn: event.turn,
            action_type: event.action_type,
            delta
          }))
      ),
    [timeline]
  );

  async function handleStart() {
    setIsLoading(true);
    setError("");
    try {
      const response = await startGame(selectedWorldId);
      setSessionId(response.session_id);
      setVisibleState(response.visible_state);
      setTurn(response.turn);
      setDialogue(null);
      setGroupScene(null);
      setSuggestedActions(["observe", "smithy", "wait"]);
      setStory([{ id: Date.now(), text: "A new local story session has started." }]);
      setLastResponse(response);
      void refreshTimeline(response.session_id);
      void refreshTimelineReplay("session", { sessionId: response.session_id });
      void refreshPlayerGraphs(response.session_id);
      void refreshDebugGraphs(response.session_id);
      void refreshNPCSimulationDebugger(response.session_id);
      void refreshGameplayModuleDebugger();
      void refreshCrashReports();
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshStudioStatus() {
    setStudioStatusError("");
    try {
      const response = await fetchStudioStatus();
      setStudioStatus(response);
    } catch (err) {
      setStudioStatus(null);
      setStudioStatusError(toErrorMessage(err));
    }
  }

  async function refreshStudioConfigSummary() {
    setStudioConfigError("");
    try {
      const response = await fetchStudioConfigSummary();
      setStudioConfigSummary(response);
    } catch (err) {
      setStudioConfigSummary(null);
      setStudioConfigError(toErrorMessage(err));
    }
  }

  async function refreshLocalConfig() {
    setStudioConfigError("");
    try {
      const [summary, issues] = await Promise.all([fetchLocalConfigSummary(), fetchLocalConfigIssues()]);
      setLocalConfigSummary(summary);
      setLocalConfigIssues(issues);
    } catch (err) {
      setLocalConfigSummary(null);
      setLocalConfigIssues([]);
      setStudioConfigError(toErrorMessage(err));
    }
  }

  async function handleGenerateLocalEnvTemplate() {
    setStudioConfigError("");
    try {
      const response = await generateLocalEnvTemplate();
      setLocalEnvTemplate(response);
    } catch (err) {
      setLocalEnvTemplate(null);
      setStudioConfigError(toErrorMessage(err));
    }
  }

  async function refreshLocalUpdateNotes() {
    setLocalUpdateNotesError("");
    try {
      const response = await fetchLocalUpdateNotes();
      setLocalUpdateNotes(response);
    } catch (err) {
      setLocalUpdateNotes(null);
      setLocalUpdateNotesError(toErrorMessage(err));
    }
  }

  async function refreshDesktopHealth() {
    setDesktopHealthError("");
    try {
      const response = await fetchDesktopHealth();
      setDesktopHealth(response);
    } catch (err) {
      setDesktopHealth(null);
      setDesktopHealthError(toErrorMessage(err));
    }
  }

  async function handleRunDesktopHealthCheck() {
    setDesktopHealthError("");
    try {
      const response = await runDesktopHealthCheck();
      setDesktopHealth(response);
    } catch (err) {
      setDesktopHealth(null);
      setDesktopHealthError(toErrorMessage(err));
    }
  }

  async function refreshLocalStudioUX() {
    setLocalStudioError("");
    try {
      const [status, config, startupChecks] = await Promise.all([
        fetchLocalStudioStatus(),
        fetchLocalStudioConfigSummary(),
        fetchLocalStudioStartupChecks()
      ]);
      setLocalStudioStatus(status);
      setLocalStudioConfig(config);
      setLocalStudioStartupChecks(startupChecks);
    } catch (err) {
      setLocalStudioStatus(null);
      setLocalStudioConfig(null);
      setLocalStudioStartupChecks(null);
      setLocalStudioError(toErrorMessage(err));
    }
  }

  async function handleBackupDryRun() {
    setBackupRestoreError("");
    try {
      setBackupPlan(await createBackupDryRun(currentNarrativeProjectId || currentWorkspaceId || "local_project"));
    } catch (err) {
      setBackupPlan(null);
      setBackupRestoreError(toErrorMessage(err));
    }
  }

  async function handleCreateBackup() {
    if (!confirmDangerousAction("Create a local backup after dry-run? Secrets, .env, logs/cache/build outputs, and mature/private content are excluded by default.")) {
      return;
    }
    setBackupRestoreError("");
    try {
      setBackupResult(await createLocalBackup(currentNarrativeProjectId || currentWorkspaceId || "local_project"));
    } catch (err) {
      setBackupResult(null);
      setBackupRestoreError(toErrorMessage(err));
    }
  }

  async function handleRestoreDryRun(backupPath: string, targetProjectId: string) {
    setBackupRestoreError("");
    try {
      setRestorePlan(await restoreBackupDryRun(backupPath, targetProjectId));
    } catch (err) {
      setRestorePlan(null);
      setBackupRestoreError(toErrorMessage(err));
    }
  }

  async function refreshRecovery() {
    setRecoveryError("");
    try {
      const [issues, plan] = await Promise.all([fetchRecoveryIssues(), buildRecoveryPlan()]);
      setRecoveryIssues(issues);
      setRecoveryPlan(plan);
    } catch (err) {
      setRecoveryIssues([]);
      setRecoveryPlan(null);
      setRecoveryError(toErrorMessage(err));
    }
  }

  async function handleDryRunRecovery() {
    setRecoveryError("");
    try {
      setRecoveryPlan(await dryRunRecovery());
    } catch (err) {
      setRecoveryPlan(null);
      setRecoveryError(toErrorMessage(err));
    }
  }

  async function refreshLocalLogs() {
    setLocalLogsError("");
    try {
      setLocalLogs(await fetchLocalLogs(50));
    } catch (err) {
      setLocalLogs(null);
      setLocalLogsError(toErrorMessage(err));
    }
  }

  async function refreshDiagnosticsBundlePreview() {
    setDiagnosticsBundleError("");
    try {
      setDiagnosticsBundlePreview(await previewDiagnosticsBundle(currentNarrativeProjectId || currentWorkspaceId || "local_project", false));
    } catch (err) {
      setDiagnosticsBundlePreview(null);
      setDiagnosticsBundleError(toErrorMessage(err));
    }
  }

  async function handlePreviewDiagnosticsBundle(includeDebug = false, explicitConfirmDebug = false) {
    setDiagnosticsBundleError("");
    setDiagnosticsBundleCreateResult(null);
    try {
      setDiagnosticsBundlePreview(await previewDiagnosticsBundle(currentNarrativeProjectId || currentWorkspaceId || "local_project", includeDebug, explicitConfirmDebug));
    } catch (err) {
      setDiagnosticsBundlePreview(null);
      setDiagnosticsBundleError(toErrorMessage(err));
    }
  }

  async function handleCreateDiagnosticsBundle(includeDebug = false, explicitConfirmDebug = false) {
    setDiagnosticsBundleError("");
    try {
      const response = await createDiagnosticsBundle(currentNarrativeProjectId || currentWorkspaceId || "local_project", includeDebug, explicitConfirmDebug);
      setDiagnosticsBundleCreateResult(response);
      setDiagnosticsBundlePreview({
        local_only: response.local_only,
        writes_file: true,
        manifest: response.manifest,
        safe_payload: {},
        warnings: response.warnings
      });
    } catch (err) {
      setDiagnosticsBundleCreateResult(null);
      setDiagnosticsBundleError(toErrorMessage(err));
    }
  }

  function dismissFirstRunOnboarding() {
    try {
      window.localStorage.setItem(FIRST_RUN_ONBOARDING_KEY, "completed");
    } catch {
      // Local browser storage may be unavailable; keep dismissal in memory.
    }
    setFirstRunDismissed(true);
  }

  async function refreshProjectWorkspaces() {
    setWorkspaceError("");
    try {
      const response = await fetchStudioWorkspaces();
      setProjectWorkspaces(response.workspaces);
      setCurrentWorkspaceId((current) => current || response.workspaces[0]?.workspace_id || "");
    } catch (err) {
      setProjectWorkspaces([]);
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function refreshNarrativeProjects() {
    setProjectShellError("");
    try {
      const response = await fetchNarrativeProjects();
      setNarrativeProjects(response.projects);
      const selected = currentNarrativeProjectId || response.projects[0]?.project_id || "";
      setCurrentNarrativeProjectId(selected);
      if (selected) {
        const modes = await fetchNarrativeProjectModes(selected);
        setProjectModeStatuses(modes.modes);
      } else {
        setProjectModeStatuses([]);
      }
    } catch (err) {
      setNarrativeProjects([]);
      setProjectModeStatuses([]);
      setProjectShellError(toErrorMessage(err));
    }
  }

  async function handleCreateNarrativeProject(projectId: string, name: string, projectRoot: string) {
    setProjectShellError("");
    setProjectShellMessage("");
    try {
      const response = await createNarrativeProject({
        project_id: projectId,
        name,
        project_root: projectRoot,
        default_world_id: selectedWorldId
      });
      await refreshNarrativeProjects();
      setCurrentNarrativeProjectId(response.project.project_id);
      setProjectShellMessage("NarrativeProject created. Novel/Tavern drafts remain separate from World GameState.");
    } catch (err) {
      setProjectShellError(toErrorMessage(err));
    }
  }

  async function handleValidateNarrativeProject(projectId: string) {
    setProjectShellError("");
    setProjectShellMessage("");
    try {
      const report = await validateNarrativeProject(projectId);
      const summary = report.summary ?? { errors: report.errors.length, warnings: report.warnings.length };
      setProjectShellMessage(`Validation ${report.ok ? "passed" : "failed"}: ${summary.errors ?? 0} errors, ${summary.warnings ?? 0} warnings.`);
    } catch (err) {
      setProjectShellError(toErrorMessage(err));
    }
  }

  async function refreshWorkspaceTemplates() {
    setWorkspaceError("");
    try {
      const response = await fetchWorkspaceTemplates();
      setWorkspaceTemplates(response.templates);
    } catch (err) {
      setWorkspaceTemplates([]);
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function refreshRecentProjects() {
    setWorkspaceError("");
    try {
      const response = await fetchRecentProjects();
      setRecentProjects(response.projects);
    } catch (err) {
      setRecentProjects([]);
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleAddWorkspace(path: string, name?: string) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    try {
      const workspace = await addStudioWorkspace(path, name || undefined);
      await refreshProjectWorkspaces();
      setCurrentWorkspaceId(workspace.workspace_id);
      setWorkspaceMessage("Workspace reference added. Active save and GameState were not changed.");
    } catch (err) {
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleCreateWorkspaceFromTemplate(templateId: WorkspaceTemplateType, path: string, name?: string) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    try {
      const workspace = await createWorkspaceFromTemplate(templateId, path, name || undefined);
      await refreshProjectWorkspaces();
      await refreshRecentProjects();
      setCurrentWorkspaceId(workspace.workspace_id);
      setWorkspaceMessage("Workspace created from local template. No secrets were copied and GameState was not changed.");
    } catch (err) {
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleSelectWorkspace(workspaceId: string) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    try {
      const workspace = await selectStudioWorkspace(workspaceId);
      setCurrentWorkspaceId(workspace.workspace_id);
      await refreshProjectWorkspaces();
      await refreshRecentProjects();
      setWorkspaceMessage("Workspace selected. This changes the studio reference only.");
    } catch (err) {
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleRemoveRecentProject(workspaceId: string) {
    setWorkspaceError("");
    setWorkspaceMessage("");
    try {
      await removeRecentProject(workspaceId);
      await refreshRecentProjects();
      setWorkspaceMessage("Recent project reference removed.");
    } catch (err) {
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleClearRecentProjects() {
    setWorkspaceError("");
    setWorkspaceMessage("");
    try {
      await clearRecentProjects();
      setRecentProjects([]);
      setWorkspaceMessage("Recent project list cleared.");
    } catch (err) {
      setWorkspaceError(toErrorMessage(err));
    }
  }

  async function handleSelectPromptProfile(profileId: string) {
    setStudioConfigError("");
    try {
      await selectPromptProfile(profileId);
      await refreshStudioConfigSummary();
    } catch (err) {
      setStudioConfigError(toErrorMessage(err));
    }
  }

  async function refreshNarrativeEvals() {
    setNarrativeEvalError("");
    try {
      const response = await fetchNarrativeEvalRecent();
      setNarrativeEvalReports(response.reports);
      setSelectedNarrativeEval((current) => current ?? response.reports[response.reports.length - 1] ?? null);
    } catch (err) {
      setNarrativeEvalReports([]);
      setNarrativeEvalError(toErrorMessage(err));
    }
  }

  async function handleRunNarrativeEval() {
    setNarrativeEvalError("");
    try {
      const report = await runNarrativeEval();
      setNarrativeEvalReports((previous) => [...previous, report]);
      setSelectedNarrativeEval(report);
    } catch (err) {
      setNarrativeEvalError(toErrorMessage(err));
    }
  }

  async function handleSelectNarrativeEval(runId: string) {
    setNarrativeEvalError("");
    try {
      const report = await fetchNarrativeEval(runId);
      setSelectedNarrativeEval(report);
    } catch (err) {
      setNarrativeEvalError(toErrorMessage(err));
    }
  }

  async function refreshPerformance() {
    setPerformanceError("");
    try {
      const [recent, summary] = await Promise.all([
        fetchDebugPerformanceRecent(),
        fetchDebugPerformanceSummary()
      ]);
      setPerformanceRecent(recent);
      setPerformanceSummary(summary);
    } catch (err) {
      setPerformanceRecent(null);
      setPerformanceSummary(null);
      setPerformanceError(toErrorMessage(err));
    }
  }

  async function refreshPlaytests() {
    setPlaytestError("");
    try {
      const response = await fetchPlaytestRecent();
      setPlaytestReports(response.reports);
      setSelectedPlaytest((current) => current ?? response.reports[response.reports.length - 1] ?? null);
    } catch (err) {
      setPlaytestReports([]);
      setSelectedPlaytest(null);
      setPlaytestError(toErrorMessage(err));
    }
  }

  async function handleRunPlaytest(options: {
    worldId: string;
    agentType: string;
    steps: number;
    seed: number;
    saveLoadCheck: boolean;
  }) {
    setPlaytestError("");
    try {
      const report = await runPlaytest({
        world_id: options.worldId,
        agent_type: options.agentType,
        steps: options.steps,
        seed: options.seed,
        save_load_check: options.saveLoadCheck,
      });
      setPlaytestReports((previous) => [...previous, report]);
      setSelectedPlaytest(report);
      void refreshStudioStatus();
    } catch (err) {
      setPlaytestError(toErrorMessage(err));
    }
  }

  async function handleRunPlaytestBatch(options: {
    worldId: string;
    agentTypes: string[];
    seeds: number[];
    steps: number;
    stopOnBlocker: boolean;
    saveLoadCheck: boolean;
  }) {
    setPlaytestError("");
    try {
      const report = await runPlaytestBatch({
        world_id: options.worldId,
        scenario_ids: [],
        agent_types: options.agentTypes,
        seeds: options.seeds,
        steps: options.steps,
        max_parallelism: 1,
        stop_on_blocker: options.stopOnBlocker,
        save_load_check: options.saveLoadCheck,
      });
      setPlaytestBatchReport(report);
      void refreshStudioStatus();
    } catch (err) {
      setPlaytestError(toErrorMessage(err));
    }
  }

  async function handleSelectPlaytest(runId: string) {
    setPlaytestError("");
    try {
      const report = await fetchPlaytest(runId);
      setSelectedPlaytest(report);
    } catch (err) {
      setPlaytestError(toErrorMessage(err));
    }
  }

  async function refreshScenarioRegressions() {
    setScenarioRegressionError("");
    try {
      const response = await fetchScenarioRegressionCases();
      setScenarioRegressionCases(response.cases);
    } catch (err) {
      setScenarioRegressionCases([]);
      setScenarioRegressionError(toErrorMessage(err));
    }
  }

  async function handleRunScenarioRegression(options: { worldId: string; scenarioIds: string[] }) {
    setScenarioRegressionError("");
    try {
      const run = await runScenarioRegression({
        world_id: options.worldId || null,
        scenario_ids: options.scenarioIds
      });
      setScenarioRegressionRuns((previous) => [...previous, run]);
      setSelectedScenarioRegressionRun(run);
    } catch (err) {
      setScenarioRegressionError(toErrorMessage(err));
    }
  }

  async function handleSelectScenarioRegression(runId: string) {
    setScenarioRegressionError("");
    const existing = scenarioRegressionRuns.find((run) => run.run_id === runId);
    if (existing) {
      setSelectedScenarioRegressionRun(existing);
      return;
    }
    try {
      const run = await fetchScenarioRegression(runId);
      setSelectedScenarioRegressionRun(run);
      setScenarioRegressionRuns((previous) => [...previous, run]);
    } catch (err) {
      setScenarioRegressionError(toErrorMessage(err));
    }
  }

  async function refreshWorldHealth() {
    setWorldHealthError("");
    try {
      const response = await fetchWorldHealth(selectedWorldId);
      setWorldHealth(response);
    } catch (err) {
      setWorldHealth(null);
      setWorldHealthError(toErrorMessage(err));
    }
  }

  async function handleRunWorldHealth() {
    setWorldHealthError("");
    try {
      const response = await runWorldHealth(selectedWorldId);
      setWorldHealth(response);
    } catch (err) {
      setWorldHealthError(toErrorMessage(err));
    }
  }

  async function refreshContentCoverage() {
    setContentCoverageError("");
    try {
      const response = await fetchContentCoverage(selectedWorldId);
      setContentCoverage(response);
    } catch (err) {
      setContentCoverage(null);
      setContentCoverageError(toErrorMessage(err));
    }
  }

  async function handleRunContentCoverage() {
    setContentCoverageError("");
    try {
      const response = await runContentCoverage(selectedWorldId);
      setContentCoverage(response);
    } catch (err) {
      setContentCoverageError(toErrorMessage(err));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || !sessionId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      if (dialogue?.dialogue_session.status === "active") {
        const response = await continueDialogue(dialogue.dialogue_session.session_id, trimmedInput);
        applyDialogueResponse(response);
      } else {
        const response = await submitPlayerInput(sessionId, trimmedInput);
        applyGameInputResponse(response);
      }
      setRecentWorldActions((previous) => [trimmedInput, ...previous.filter((action) => action !== trimmedInput)].slice(0, 8));
      setInput("");
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartDialogue(focusNpcId: string, dialogueMode = selectedDialogueMode) {
    if (!sessionId || isLoading) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const response = await startDialogue(sessionId, focusNpcId, dialogueMode, sceneMoodPresetId);
      applyDialogueResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleEndDialogue() {
    if (!dialogue || isLoading) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const response = await endDialogue(dialogue.dialogue_session.session_id);
      applyDialogueResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartGroupScene(participantIds: string[], sceneTopic = "local scene", sceneMood = "neutral") {
    if (!sessionId || isLoading) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const response = await startGroupDialogue(sessionId, participantIds, sceneTopic, sceneMood, sceneMoodPresetId);
      applyGroupSceneResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleNextGroupSpeaker() {
    if (!groupScene || isLoading) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const response = await selectGroupDialogueNextSpeaker(groupScene.scene.scene_id);
      applyGroupSceneResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleEndGroupScene() {
    if (!groupScene || isLoading) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      const response = await endGroupDialogue(groupScene.scene.scene_id);
      applyGroupSceneResponse(response);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleRefreshState() {
    if (!sessionId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await fetchGameState(sessionId);
      setVisibleState(response.visible_state);
      setTurn(response.turn);
      setLastResponse(response);
      void refreshTimeline(sessionId);
      void refreshTimelineReplay("session", { sessionId });
      void refreshPlayerGraphs(sessionId);
      void refreshDebugGraphs(sessionId);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    if (!sessionId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await saveGame(sessionId);
      setLastResponse(response);
      await refreshSaves(response.save_id);
      void refreshSaveTimeline(response.save_id);
      void refreshTimelineReplay("save", { saveId: response.save_id });
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLoad() {
    if (!selectedSaveId || isLoading) {
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await loadGame(selectedSaveId);
      setSessionId(response.session_id);
      setVisibleState(response.visible_state);
      setTurn(response.turn);
      setDialogue(null);
      setGroupScene(null);
      setSuggestedActions(["observe", "smithy", "wait"]);
      setStory([{ id: Date.now(), text: `Loaded save ${response.save_id}.` }]);
      setLastResponse(response);
      void refreshTimeline(response.session_id);
      void refreshTimelineReplay("session", { sessionId: response.session_id });
      void refreshPlayerGraphs(response.session_id);
      void refreshDebugGraphs(response.session_id);
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeleteSave(saveId = selectedSaveId) {
    if (!saveId || isLoading) {
      return;
    }
    const confirmed = confirmDangerousAction(`${DANGEROUS_ACTION_COPY.deleteSave} Save id: ${saveId}`);
    if (!confirmed) {
      return;
    }
    setIsLoading(true);
    setError("");
    try {
      await deleteSave(saveId);
      await refreshSaves(selectedSaveId === saveId ? undefined : selectedSaveId);
      if (selectedSaveId === saveId) {
        setSelectedSaveId("");
      }
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  async function handleExportSave(saveId = selectedSaveId) {
    if (!saveId || isLoading) {
      return;
    }
    setMigrationError("");
    try {
      const exported = await exportSaveArchive(saveId);
      window.alert(`Save bundle ready: ${exported.file_name}. Use the API response archive_base64 with the local import endpoint.`);
    } catch (err) {
      setMigrationError(toErrorMessage(err));
    }
  }

  async function refreshSaves(nextSelectedSaveId?: string, worldFilter = saveWorldFilter) {
    const response = await listSaves(worldFilter || undefined);
    setSaves(response.saves);
    setSelectedSaveId(nextSelectedSaveId ?? response.saves[0]?.save_id ?? "");
  }

  async function handleCheckMigration(saveId = selectedSaveId) {
    if (!saveId || isLoading) {
      return;
    }
    setMigrationError("");
    try {
      const status = await fetchSaveMigrationStatus(saveId);
      setMigrationStatusBySaveId((previous) => ({ ...previous, [saveId]: status }));
    } catch (err) {
      setMigrationError(toErrorMessage(err));
    }
  }

  async function handleDryRunMigration(saveId = selectedSaveId) {
    if (!saveId || isLoading) {
      return;
    }
    setMigrationError("");
    try {
      const result = await dryRunSaveMigration(saveId);
      setMigrationResultBySaveId((previous) => ({ ...previous, [saveId]: result }));
      await handleCheckMigration(saveId);
    } catch (err) {
      setMigrationError(toErrorMessage(err));
    }
  }

  async function handleApplyMigration(saveId = selectedSaveId) {
    if (!saveId || isLoading) {
      return;
    }
    const confirmed = confirmDangerousAction(DANGEROUS_ACTION_COPY.applyMigration);
    if (!confirmed) {
      return;
    }
    setIsLoading(true);
    setMigrationError("");
    try {
      const result = await applySaveMigration(saveId);
      setMigrationResultBySaveId((previous) => ({ ...previous, [saveId]: result }));
      await handleCheckMigration(saveId);
      await refreshSaves(saveId);
    } catch (err) {
      setMigrationError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  function applyGameInputResponse(response: GameInputResponse) {
    setStory((entries) => [
      ...entries,
      {
        id: Date.now(),
        text: response.narrative_text
      }
    ]);
    setSuggestedActions(response.suggested_actions);
    setVisibleState(response.visible_state);
    setTurn(response.turn);
    setLastResponse(response);
    void refreshTimeline(sessionId);
    void refreshTimelineReplay("session", { sessionId });
    void refreshPlayerGraphs(sessionId);
    void refreshDebugGraphs(sessionId);
    void refreshNPCSimulationDebugger(sessionId);
  }

  function applyDialogueResponse(response: DialogueModeResponse) {
    setDialogue(response);
    setStory((entries) => [
      ...entries,
      {
        id: Date.now(),
        text: response.narrative_text
      }
    ]);
    setVisibleState(response.visible_state);
    setTurn(response.turn);
    setSuggestedActions(response.dialogue_session.status === "active" ? ["ask about rumors", "thank you", "goodbye"] : []);
    setLastResponse(response);
    void refreshTimeline(sessionId);
    void refreshTimelineReplay("session", { sessionId });
    void refreshPlayerGraphs(sessionId);
    void refreshDebugGraphs(sessionId);
    void refreshNPCSimulationDebugger(sessionId);
  }

  function applyGroupSceneResponse(response: GroupDialogueSceneResponse) {
    setGroupScene(response);
    setStory((entries) => [
      ...entries,
      {
        id: Date.now(),
        text: response.narrative_text
      }
    ]);
    setVisibleState(response.visible_state);
    setTurn(response.turn);
    setLastResponse(response);
    void refreshTimeline(sessionId);
    void refreshTimelineReplay("session", { sessionId });
    void refreshPlayerGraphs(sessionId);
    void refreshDebugGraphs(sessionId);
  }

  async function refreshTimeline(nextSessionId = sessionId) {
    if (!nextSessionId) {
      return;
    }
    setTimelineError("");
    try {
      const response = await fetchSessionDebugEvents(nextSessionId);
      setTimeline(response.events);
    } catch (err) {
      setTimeline([]);
      setTimelineError(toErrorMessage(err));
    }
  }

  async function refreshSaveTimeline(saveId = selectedSaveId) {
    if (!saveId) {
      return;
    }
    setTimelineError("");
    try {
      const response = await fetchSaveDebugEvents(saveId);
      setTimeline(response.events);
    } catch (err) {
      setTimeline([]);
      setTimelineError(toErrorMessage(err));
    }
  }

  async function refreshTimelineReplay(
    source: "session" | "save" = timelineReplaySource,
    options?: { sessionId?: string; saveId?: string }
  ) {
    const nextSessionId = options?.sessionId ?? sessionId;
    const nextSaveId = options?.saveId ?? selectedSaveId;
    if (source === "session" && !nextSessionId) {
      return;
    }
    if (source === "save" && !nextSaveId) {
      return;
    }
    setTimelineReplayError("");
    setTimelineReplayDryRunError("");
    try {
      const response =
        source === "session"
          ? await fetchSessionTimelineReplay(nextSessionId)
          : await fetchSaveTimelineReplay(nextSaveId);
      setTimelineReplay(response);
      setTimelineReplaySource(source);
      if (source === "session") {
        setTimelineReplayDryRun(null);
      }
    } catch (err) {
      setTimelineReplay(null);
      setTimelineReplayError(toErrorMessage(err));
    }
  }

  async function handleReplayDryRun() {
    if (!selectedSaveId) {
      setTimelineReplayDryRunError("Select a save before running replay dry-run.");
      return;
    }
    setTimelineReplayDryRunError("");
    try {
      const response = await dryRunSaveTimelineReplay(selectedSaveId);
      setTimelineReplayDryRun(response);
      setTimelineReplay(response);
      setTimelineReplaySource("save");
    } catch (err) {
      setTimelineReplayDryRun(null);
      setTimelineReplayDryRunError(toErrorMessage(err));
    }
  }

  async function refreshPlayerGraphs(nextSessionId = sessionId) {
    if (!nextSessionId) {
      return;
    }
    setGraphError("");
    try {
      const [relationshipGraph, factionGraph] = await Promise.all([
        fetchPlayerRelationshipGraph(nextSessionId),
        fetchPlayerFactionGraph(nextSessionId)
      ]);
      setPlayerRelationshipGraph(filterPlayerGraph(relationshipGraph));
      setPlayerFactionGraph(filterPlayerGraph(factionGraph));
    } catch (err) {
      setPlayerRelationshipGraph(null);
      setPlayerFactionGraph(null);
      setGraphError(toErrorMessage(err));
    }
  }

  async function refreshDebugGraphs(nextSessionId = sessionId) {
    if (!nextSessionId) {
      return;
    }
    setDebugGraphError("");
    try {
      const [relationshipGraph, factionGraph] = await Promise.all([
        fetchDebugRelationshipGraph(nextSessionId),
        fetchDebugFactionGraph(nextSessionId)
      ]);
      setDebugRelationshipGraph(relationshipGraph);
      setDebugFactionGraph(factionGraph);
    } catch (err) {
      setDebugRelationshipGraph(null);
      setDebugFactionGraph(null);
      setDebugGraphError(toErrorMessage(err));
    }
  }

  async function refreshNPCSimulationDebugger(nextSessionId = sessionId, nextNPCId = selectedSimulationNPCId) {
    if (!nextSessionId) {
      return;
    }
    setNPCSimulationError("");
    try {
      const [summaryResponse, tickResponse] = await Promise.all([
        fetchNPCSimulationDebug(nextSessionId),
        fetchNPCSimulationDebugTicks(nextSessionId)
      ]);
      setNPCSimulationSummaries(summaryResponse.npcs);
      setNPCSimulationEvents(tickResponse.ticks);
      const selectedId = nextNPCId || summaryResponse.npcs[0]?.npc_id || "";
      setSelectedSimulationNPCId(selectedId);
      if (selectedId) {
        const detail = await fetchNPCSimulationDebugDetail(nextSessionId, selectedId);
        setNPCSimulationDetail(detail);
        await refreshNPCBehaviorTimeline(nextSessionId, selectedId);
      } else {
        setNPCSimulationDetail(null);
        setNPCBehaviorTimeline(null);
      }
    } catch (err) {
      setNPCSimulationSummaries([]);
      setNPCSimulationDetail(null);
      setNPCSimulationEvents([]);
      setNPCSimulationError(toErrorMessage(err));
    }
  }

  async function handleSelectSimulationNPC(npcId: string) {
    setSelectedSimulationNPCId(npcId);
    setNPCSimulationError("");
    setNPCSimulationDryRun(null);
    if (!sessionId || !npcId) {
      setNPCSimulationDetail(null);
      return;
    }
    try {
      const detail = await fetchNPCSimulationDebugDetail(sessionId, npcId);
      setNPCSimulationDetail(detail);
      await refreshNPCBehaviorTimeline(sessionId, npcId);
    } catch (err) {
      setNPCSimulationDetail(null);
      setNPCSimulationError(toErrorMessage(err));
    }
  }

  async function handleNPCSimulationDryRun() {
    if (!sessionId) {
      setNPCSimulationError("Start or load a session before running NPC simulation dry-run.");
      return;
    }
    setNPCSimulationError("");
    try {
      const response = await dryRunNPCSimulationTick(sessionId);
      setNPCSimulationDryRun(response);
      await refreshNPCSimulationDebugger(sessionId, selectedSimulationNPCId);
    } catch (err) {
      setNPCSimulationDryRun(null);
      setNPCSimulationError(toErrorMessage(err));
    }
  }

  async function refreshGameplayModuleDebugger(nextModuleId = selectedModuleDebugId) {
    setModuleDebugError("");
    try {
      const response = await fetchGameplayModuleDebug();
      setModuleDebugSummaries(response.modules);
      const selectedId = nextModuleId || response.modules[0]?.module_id || "";
      setSelectedModuleDebugId(selectedId);
      if (selectedId) {
        setModuleDebugDetail(await fetchGameplayModuleDebugDetail(selectedId));
      } else {
        setModuleDebugDetail(null);
      }
    } catch (err) {
      setModuleDebugSummaries([]);
      setModuleDebugDetail(null);
      setModuleDebugError(toErrorMessage(err));
    }
  }

  async function refreshCrashReports(nextReportId = selectedCrashReportId) {
    setCrashReportError("");
    try {
      const response = await fetchCrashReports();
      setCrashReports(response.reports);
      const selectedId = nextReportId || response.reports[0]?.id || "";
      setSelectedCrashReportId(selectedId);
      if (selectedId) {
        setSelectedCrashReport(await fetchCrashReport(selectedId));
      } else {
        setSelectedCrashReport(null);
      }
    } catch (err) {
      setCrashReports([]);
      setSelectedCrashReport(null);
      setCrashReportError(toErrorMessage(err));
    }
  }

  async function handleSelectCrashReport(reportId: string) {
    setSelectedCrashReportId(reportId);
    setCrashReportError("");
    try {
      setSelectedCrashReport(await fetchCrashReport(reportId));
    } catch (err) {
      setSelectedCrashReport(null);
      setCrashReportError(toErrorMessage(err));
    }
  }

  async function handleDeleteCrashReport(reportId: string) {
    setCrashReportError("");
    try {
      await deleteCrashReport(reportId);
      await refreshCrashReports("");
    } catch (err) {
      setCrashReportError(toErrorMessage(err));
    }
  }

  async function handleSelectGameplayModule(moduleId: string) {
    setSelectedModuleDebugId(moduleId);
    setModuleDebugDryRun(null);
    setModuleDebugError("");
    if (!moduleId) {
      setModuleDebugDetail(null);
      return;
    }
    try {
      setModuleDebugDetail(await fetchGameplayModuleDebugDetail(moduleId));
    } catch (err) {
      setModuleDebugDetail(null);
      setModuleDebugError(toErrorMessage(err));
    }
  }

  async function handleGameplayModuleDryRun(actionId: string) {
    if (!selectedModuleDebugId) {
      setModuleDebugError("Select a module before running action dry-run.");
      return;
    }
    setModuleDebugError("");
    try {
      setModuleDebugDryRun(await dryRunGameplayModuleAction(selectedModuleDebugId, actionId));
    } catch (err) {
      setModuleDebugDryRun(null);
      setModuleDebugError(toErrorMessage(err));
    }
  }

  async function refreshNPCBehaviorTimeline(nextSessionId = sessionId, nextNPCId = selectedSimulationNPCId) {
    if (!nextSessionId || !nextNPCId) {
      setNPCBehaviorTimeline(null);
      return;
    }
    setNPCBehaviorTimelineError("");
    try {
      const turnFrom = npcBehaviorTurnFrom.trim() ? Number(npcBehaviorTurnFrom) : null;
      const turnTo = npcBehaviorTurnTo.trim() ? Number(npcBehaviorTurnTo) : null;
      const response = await fetchNPCBehaviorTimeline(nextSessionId, nextNPCId, turnFrom, turnTo);
      setNPCBehaviorTimeline(response);
    } catch (err) {
      setNPCBehaviorTimeline(null);
      setNPCBehaviorTimelineError(toErrorMessage(err));
    }
  }

  return (
    <main className="app-shell">
      <aside className="side-panel">
        <div>
          <h1>Mist Valley</h1>
          <p className="muted">Local interactive novel prototype</p>
        </div>

        <section>
          <h2>Local Navigation</h2>
          <UnifiedNavigation
            mode={mode}
            requestedTool={requestedAuthoringTool}
            hasProject={Boolean(currentNarrativeProjectId)}
            debugEnabled={studioStatus?.debug_api_enabled ?? false}
            debugOpen={debugOpen}
            onNavigate={(targetMode, toolId) => {
              if (toolId) {
                setRequestedAuthoringTool(toolId);
              }
              setMode(targetMode);
            }}
            onToggleDebug={() => setDebugOpen((current) => !current)}
          />
        </section>

        {mode === "play" && (
          <>
        <section>
          <h2>World</h2>
          <select
            value={selectedWorldId}
            onChange={(event) => setSelectedWorldId(event.target.value)}
            disabled={isLoading}
          >
            {WORLD_OPTIONS.map((world) => (
              <option key={world.id} value={world.id}>
                {world.name}
              </option>
            ))}
          </select>
          <button type="button" onClick={handleStart} disabled={isLoading}>
            Start
          </button>
        </section>

        <SaveBrowser
          saves={saves}
          selectedSaveId={selectedSaveId}
          migrationStatusBySaveId={migrationStatusBySaveId}
          migrationResultBySaveId={migrationResultBySaveId}
          migrationError={migrationError}
          saveWorldFilter={saveWorldFilter}
          isLoading={isLoading}
          onSave={handleSave}
          onLoad={handleLoad}
          onDelete={(saveId) => void handleDeleteSave(saveId)}
          onRefresh={() => void refreshSaves(selectedSaveId)}
          onCheckMigration={(saveId) => void handleCheckMigration(saveId)}
          onDryRunMigration={(saveId) => void handleDryRunMigration(saveId)}
          onApplyMigration={(saveId) => void handleApplyMigration(saveId)}
          onExportSave={(saveId) => void handleExportSave(saveId)}
          onSelectSave={setSelectedSaveId}
          onFilterWorld={(worldId) => {
            setSaveWorldFilter(worldId);
            void refreshSaves(undefined, worldId);
          }}
        />

        <section>
          <h2>Location</h2>
          <p>{visibleState?.location.name ?? "Not started"}</p>
        </section>

        <section>
          <h2>Dialogue</h2>
          <DialogueModePanel
            dialogue={dialogue}
            groupScene={groupScene}
            visibleState={visibleState}
            configSummary={studioConfigSummary}
            configError={studioConfigError}
            isLoading={isLoading}
            selectedMoodPresetId={sceneMoodPresetId}
            onSelectMoodPreset={setSceneMoodPresetId}
            selectedDialogueMode={selectedDialogueMode}
            onSelectDialogueMode={setSelectedDialogueMode}
            onSelectPromptProfile={(profileId) => void handleSelectPromptProfile(profileId)}
            onStart={(npcId, dialogueMode) => void handleStartDialogue(npcId, dialogueMode)}
            onEnd={() => void handleEndDialogue()}
            onStartGroup={(npcIds, sceneTopic, sceneMood) => void handleStartGroupScene(npcIds, sceneTopic, sceneMood)}
            onNextGroupSpeaker={() => void handleNextGroupSpeaker()}
            onEndGroup={() => void handleEndGroupScene()}
          />
        </section>

        <section>
          <h2>Time</h2>
          <p>{visibleState?.time.formatted ?? "Not started"}</p>
          <p className="muted">Turn {turn}</p>
        </section>

        <section>
          <h2>Inventory</h2>
          <p className="muted">
            {visibleState?.inventory.length
              ? visibleState.inventory.map((item) => item.id).join(", ")
              : "Empty"}
          </p>
        </section>

        <section>
          <h2>Quests</h2>
          <ItemList
            emptyText="None"
            items={(visibleState?.quests ?? []).map((quest) => (
              <span key={quest.id}>
                {quest.name} ({quest.status})
              </span>
            ))}
          />
        </section>

        <section>
          <h2>Social</h2>
          <SocialPanel visibleState={visibleState} />
        </section>

        <section>
          <h2>Graphs</h2>
          <ErrorPanel message={graphError} compact />
          <GraphPanel
            title="Relationships"
            graph={playerRelationshipGraph}
            emptyText="No known relationships."
          />
          <GraphPanel
            title="Factions"
            graph={playerFactionGraph}
            emptyText="No known faction links."
          />
        </section>

        <section>
          <h2>Status</h2>
          <StatusPanel visibleState={visibleState} />
        </section>
          </>
        )}
      </aside>

      <section className="story-panel">
        {!firstRunDismissed && (
          <FirstRunOnboardingFlow
            hasProject={Boolean(currentNarrativeProjectId || currentWorkspaceId)}
            onOpenProjectHome={() => setMode("project")}
            onOpenProviderSetup={() => setMode("prompt_lab")}
            onSkip={dismissFirstRunOnboarding}
            onComplete={dismissFirstRunOnboarding}
          />
        )}
        {mode === "project" ? (
          <ProjectShell
            projects={narrativeProjects}
            selectedProjectId={currentNarrativeProjectId}
            modeStatuses={projectModeStatuses}
            error={projectShellError}
            message={projectShellMessage}
            onRefresh={() => void refreshNarrativeProjects()}
            onSelect={(projectId) => {
              setCurrentNarrativeProjectId(projectId);
              void fetchNarrativeProjectModes(projectId).then((response) => setProjectModeStatuses(response.modes)).catch((err) => setProjectShellError(toErrorMessage(err)));
            }}
            onCreate={(projectId, name, root) => void handleCreateNarrativeProject(projectId, name, root)}
            onValidate={(projectId) => void handleValidateNarrativeProject(projectId)}
          />
        ) : mode === "authoring" ? (
          <AuthoringPanel
            projectId={currentNarrativeProjectId || "local_project"}
            requestedTool={requestedAuthoringTool}
            onRequestedToolHandled={() => setRequestedAuthoringTool(null)}
          />
        ) : mode === "prompt_lab" ? (
          <PromptLabPage
            summary={studioConfigSummary}
            configError={studioConfigError}
            projectId={currentNarrativeProjectId || "local_project"}
            onSelectPromptProfile={(profileId) => void handleSelectPromptProfile(profileId)}
          />
        ) : mode === "studio" ? (
          <StudioHome
            status={studioStatus}
            selectedProjectId={currentNarrativeProjectId}
            configSummary={studioConfigSummary}
            localConfigSummary={localConfigSummary}
            localConfigIssues={localConfigIssues}
            localEnvTemplate={localEnvTemplate}
            localUpdateNotes={localUpdateNotes}
            desktopHealth={desktopHealth}
            localStudioStatus={localStudioStatus}
            localStudioConfig={localStudioConfig}
            localStudioStartupChecks={localStudioStartupChecks}
            localStudioError={localStudioError}
            backupPlan={backupPlan}
            backupResult={backupResult}
            restorePlan={restorePlan}
            backupRestoreError={backupRestoreError}
            recoveryIssues={recoveryIssues}
            recoveryPlan={recoveryPlan}
            recoveryError={recoveryError}
            localLogs={localLogs}
            localLogsError={localLogsError}
            diagnosticsBundlePreview={diagnosticsBundlePreview}
            diagnosticsBundleCreateResult={diagnosticsBundleCreateResult}
            diagnosticsBundleError={diagnosticsBundleError}
            workspaces={projectWorkspaces}
            workspaceTemplates={workspaceTemplates}
            recentProjects={recentProjects}
            currentWorkspaceId={currentWorkspaceId}
            saves={saves}
            narrativeEvalReports={narrativeEvalReports}
            selectedNarrativeEval={selectedNarrativeEval}
            performanceRecent={performanceRecent}
            performanceSummary={performanceSummary}
            playtestReports={playtestReports}
            selectedPlaytest={selectedPlaytest}
            playtestBatchReport={playtestBatchReport}
            scenarioRegressionCases={scenarioRegressionCases}
            scenarioRegressionRuns={scenarioRegressionRuns}
            selectedScenarioRegressionRun={selectedScenarioRegressionRun}
            worldHealth={worldHealth}
            contentCoverage={contentCoverage}
            error={studioStatusError}
            workspaceError={workspaceError}
            workspaceMessage={workspaceMessage}
            configError={studioConfigError}
            updateNotesError={localUpdateNotesError}
            desktopHealthError={desktopHealthError}
            narrativeEvalError={narrativeEvalError}
            performanceError={performanceError}
            playtestError={playtestError}
            scenarioRegressionError={scenarioRegressionError}
            worldHealthError={worldHealthError}
            contentCoverageError={contentCoverageError}
            onRefresh={() => {
              void refreshStudioStatus();
              void refreshStudioConfigSummary();
              void refreshLocalConfig();
              void refreshLocalUpdateNotes();
              void refreshDesktopHealth();
              void refreshLocalStudioUX();
              void refreshRecovery();
              void refreshLocalLogs();
              void refreshDiagnosticsBundlePreview();
              void refreshProjectWorkspaces();
              void refreshWorkspaceTemplates();
              void refreshRecentProjects();
              void refreshSaves();
              void refreshNarrativeEvals();
              void refreshPerformance();
              void refreshPlaytests();
              void refreshWorldHealth();
              void refreshContentCoverage();
            }}
            onAddWorkspace={(path, name) => void handleAddWorkspace(path, name)}
            onCreateWorkspaceFromTemplate={(templateId, path, name) => void handleCreateWorkspaceFromTemplate(templateId, path, name)}
            onSelectWorkspace={(workspaceId) => void handleSelectWorkspace(workspaceId)}
            onRemoveRecentProject={(workspaceId) => void handleRemoveRecentProject(workspaceId)}
            onClearRecentProjects={() => void handleClearRecentProjects()}
            onRefreshLocalConfig={() => void refreshLocalConfig()}
            onGenerateLocalEnvTemplate={() => void handleGenerateLocalEnvTemplate()}
            onRefreshUpdateNotes={() => void refreshLocalUpdateNotes()}
            onRunDesktopHealthCheck={() => void handleRunDesktopHealthCheck()}
            onRefreshLocalStudio={() => void refreshLocalStudioUX()}
            onBackupDryRun={() => void handleBackupDryRun()}
            onCreateBackup={() => void handleCreateBackup()}
            onRestoreDryRun={(backupPath, targetProjectId) => void handleRestoreDryRun(backupPath, targetProjectId)}
            onRefreshRecovery={() => void refreshRecovery()}
            onDryRunRecovery={() => void handleDryRunRecovery()}
            onRefreshLocalLogs={() => void refreshLocalLogs()}
            onPreviewDiagnosticsBundle={() => void refreshDiagnosticsBundlePreview()}
            onPreviewDiagnosticsBundleWithOptions={(includeDebug, explicitConfirmDebug) => void handlePreviewDiagnosticsBundle(includeDebug, explicitConfirmDebug)}
            onCreateDiagnosticsBundle={(includeDebug, explicitConfirmDebug) => void handleCreateDiagnosticsBundle(includeDebug, explicitConfirmDebug)}
            onSelectPromptProfile={(profileId) => void handleSelectPromptProfile(profileId)}
            onRunNarrativeEval={() => void handleRunNarrativeEval()}
            onSelectNarrativeEval={(runId) => void handleSelectNarrativeEval(runId)}
            onRefreshPerformance={() => void refreshPerformance()}
            onRunPlaytest={(options) => void handleRunPlaytest(options)}
            onRunPlaytestBatch={(options) => void handleRunPlaytestBatch(options)}
            onSelectPlaytest={(runId) => void handleSelectPlaytest(runId)}
            onRefreshPlaytests={() => void refreshPlaytests()}
            onRunScenarioRegression={(options) => void handleRunScenarioRegression(options)}
            onSelectScenarioRegression={(runId) => void handleSelectScenarioRegression(runId)}
            onRefreshScenarioRegressions={() => void refreshScenarioRegressions()}
            onRunWorldHealth={() => void handleRunWorldHealth()}
            onRefreshWorldHealth={() => void refreshWorldHealth()}
            onRunContentCoverage={() => void handleRunContentCoverage()}
            onRefreshContentCoverage={() => void refreshContentCoverage()}
            onNavigate={(nextMode, toolId) => {
              if (toolId) {
                setRequestedAuthoringTool(toolId);
              }
              setMode(nextMode);
            }}
          />
        ) : (
          <WorldWorkspaceShell
            visibleState={visibleState}
            sessionId={sessionId}
            debugEnabled={studioStatus?.debug_api_enabled ?? false}
            providerSummary={studioConfigSummary?.provider_status ?? studioConfigSummary?.llm_provider ?? "Provider Gateway"}
            left={
              <>
                <WorldWorkspaceNavigation
                  visibleState={visibleState}
                  debugEnabled={studioStatus?.debug_api_enabled ?? false}
                  onJump={(targetId) => {
                    const target = document.getElementById(targetId);
                    target?.scrollIntoView({ behavior: "smooth", block: "start" });
                  }}
                />
                <WorldStudioLanding
                  visibleState={visibleState}
                  sessionId={sessionId}
                  selectedSaveId={selectedSaveId}
                  saves={saves}
                  debugEnabled={studioStatus?.debug_api_enabled ?? false}
                />
                <LocationCard visibleState={visibleState} onAction={setInput} />
                <NPCRelationshipPanel visibleState={visibleState} onAction={setInput} />
                <QuestJournalPanel visibleState={visibleState} />
                <InventoryTradePanel visibleState={visibleState} onAction={setInput} />
              </>
            }
            main={
              <>
                <WorldPlayMainView>
                  <PageHeader
                    eyebrow="World Play Main View Pro"
                    title="Story / Narration"
                    description="Narration renders confirmed backend results. Normal view excludes hidden facts, NPC secrets, raw state_deltas, raw prompts, and API keys."
                  />
                  <div className="story-scroll">
                    {story.map((entry) => (
                      <article className="story-entry" key={entry.id}>
                        {entry.text}
                      </article>
                    ))}
                    {story.length === 0 && <EmptyState title="No active story yet." detail="Start a local session. The player view only uses visible_state returned by the backend." />}
                  </div>
                  <WorldActionInputPanel
                    input={input}
                    suggestedActions={suggestedActions}
                    recentActions={recentWorldActions}
                    category={worldActionCategory}
                    isLoading={isLoading}
                    hasSession={Boolean(sessionId)}
                    placeholder={dialogue?.dialogue_session.status === "active" ? "Say something in dialogue..." : "Enter your action..."}
                    onInputChange={setInput}
                    onCategoryChange={setWorldActionCategory}
                    onSelectAction={setInput}
                    onSubmit={handleSubmit}
                  />
                  <ErrorPanel message={error} />
                </WorldPlayMainView>
                <TacticalCombatPanel visibleState={visibleState} onAction={setInput} />
                <EconomyDashboardPanel visibleState={visibleState} />
                <FactionWarDashboardPanel visibleState={visibleState} />
                <DeductionBoardPanel visibleState={visibleState} onAction={setInput} />
                <SurvivalTravelPanel visibleState={visibleState} onAction={setInput} />
                <WorldAdvancedModulePanels visibleState={visibleState} onAction={setInput} />
                <WorldTimelineEventLogPanel events={timeline} debugEnabled={studioStatus?.debug_api_enabled ?? false} />
                <WorldSaveLoadPanel
                  saves={saves}
                  selectedSaveId={selectedSaveId}
                  migrationStatusBySaveId={migrationStatusBySaveId}
                  onSelectSave={setSelectedSaveId}
                  onSaveCurrent={() => void handleSave()}
                  onLoadSelected={() => void handleLoad()}
                  onDeleteSelected={() => void handleDeleteSave(selectedSaveId)}
                  onRefresh={() => void refreshSaves(selectedSaveId)}
                  hasSession={Boolean(sessionId)}
                  busy={isLoading}
                />
                <WorldQualityPlaytestPanel
                  worldHealthStatus={worldHealth ? `${worldHealth.overall_score}` : "not run"}
                  playtestCount={playtestReports.length}
                  onRunWorldHealth={() => void handleRunWorldHealth()}
                  onRunPlaytest={() => void handleRunPlaytest({
                    worldId: selectedWorldId,
                    agentType: "curious",
                    steps: 20,
                    seed: 123,
                    saveLoadCheck: false
                  })}
                  onOpenQuality={() => setMode("studio")}
                />
              </>
            }
            right={
              <>
                <VisibleStateInspector visibleState={visibleState} />
                <WorldPromptProviderPanel
                  configSummary={studioConfigSummary}
                  onOpenProviderSetup={() => setMode("prompt_lab")}
                />
                <section className="section-card player">
                  <h3>Advanced World Modules</h3>
                  <div className="chip-list">
                    {["tactical_combat", "economy_sim", "faction_war", "deduction", "survival_travel", "magic", "hacking", "crafting", "cultivation"].map((moduleId) => (
                      <ModuleStatusBadge key={moduleId} label={moduleId} enabled={Boolean(sessionId)} />
                    ))}
                  </div>
                  <p className="muted">Module UI cannot change module rules, calculate outcomes, or bypass ActionRegistry.</p>
                </section>
              </>
            }
          />
        )}
      </section>

      <aside className={`debug-panel ${debugOpen ? "open" : "closed"}`}>
        <button className="debug-toggle" type="button" onClick={() => setDebugOpen(!debugOpen)}>
          {debugOpen ? "Hide Debug" : "Debug"}
        </button>

        {debugOpen && (
          <div className="debug-content">
            <TimelineReplayPanel
              timeline={timelineReplay}
              source={timelineReplaySource}
              selectedSaveId={selectedSaveId}
              selectedFilter={timelineReplayFilter}
              onFilterChange={setTimelineReplayFilter}
              onLoadSession={() => void refreshTimelineReplay("session")}
              onLoadSave={() => void refreshTimelineReplay("save")}
              onDryRun={() => void handleReplayDryRun()}
              error={timelineReplayError}
              dryRun={timelineReplayDryRun}
              dryRunError={timelineReplayDryRunError}
              debugEnabled={studioStatus?.debug_api_enabled ?? false}
            />
            <EventLogViewerPanel
              events={timeline}
              error={timelineError}
              selectedSaveId={selectedSaveId}
              hasSession={Boolean(sessionId)}
              onLoadSession={() => void refreshTimeline()}
              onLoadSave={() => void refreshSaveTimeline()}
              debugEnabled={studioStatus?.debug_api_enabled ?? false}
            />
            <HiddenLeakReportPanel
              visibleState={visibleState}
              events={timeline}
              worldHealth={worldHealth}
              narrativeEvalReports={narrativeEvalReports}
              diagnosticsBundlePreview={diagnosticsBundlePreview}
              backupPlan={backupPlan}
              selectedWorldId={selectedWorldId}
              onRunLeakCheck={() => void handleRunWorldHealth()}
            />
            <DebugGate debugEnabled={studioStatus?.debug_api_enabled ?? false}>
            <LocalOnlyNotice>
              Debug data is local-only and separate from player narrative. Raw event deltas stay in this panel.
            </LocalOnlyNotice>
            <button type="button" onClick={handleRefreshState} disabled={!sessionId || isLoading}>
              Refresh State
            </button>
            <button type="button" onClick={() => void refreshSaves()} disabled={isLoading}>
              Refresh Saves
            </button>
            <button type="button" onClick={() => void refreshTimeline()} disabled={!sessionId || isLoading}>
              Refresh Timeline
            </button>
            <button
              type="button"
              onClick={() => void refreshTimelineReplay("session")}
              disabled={!sessionId || isLoading}
            >
              Load Session Replay
            </button>
            <button type="button" onClick={() => void refreshDebugGraphs()} disabled={!sessionId || isLoading}>
              Refresh Graphs
            </button>
            <button type="button" onClick={() => void refreshNPCSimulationDebugger()} disabled={!sessionId || isLoading}>
              Refresh NPC Simulation
            </button>
            <button type="button" onClick={() => void refreshGameplayModuleDebugger()} disabled={isLoading}>
              Refresh Gameplay Modules
            </button>
            <button type="button" onClick={() => void refreshCrashReports()} disabled={isLoading}>
              Refresh Crash Reports
            </button>
            <button
              type="button"
              onClick={() => void refreshSaveTimeline()}
              disabled={!selectedSaveId || isLoading}
            >
              Load Save Timeline
            </button>
            <button
              type="button"
              onClick={() => void refreshTimelineReplay("save")}
              disabled={!selectedSaveId || isLoading}
            >
              Load Save Replay
            </button>
            <button
              type="button"
              onClick={() => void handleReplayDryRun()}
              disabled={!selectedSaveId || isLoading}
            >
              Replay Dry-Run
            </button>
            <dl>
              <dt>Session</dt>
              <dd>{sessionId || "Not created"}</dd>
              <dt>Visible Objects</dt>
              <dd>
                {visibleState?.visible_objects.length
                  ? visibleState.visible_objects.map((item) => item.id).join(", ")
                  : "None"}
              </dd>
              <dt>Visible NPCs</dt>
              <dd>
                {visibleState?.visible_npcs.length
                  ? visibleState.visible_npcs.map((npc) => npc.id).join(", ")
                  : "None"}
              </dd>
              <dt>Known Facts</dt>
              <dd>{knownFacts.length > 0 ? knownFacts.map((fact) => fact.id).join(", ") : "None"}</dd>
            </dl>
            <section className="debug-group">
              <h2>Debug Graphs</h2>
              {debugGraphError && <p className="error">{debugGraphError}</p>}
              {debugGraphError && debugGraphError.toLowerCase().includes("debug") && (
                <p className="muted">debug disabled</p>
              )}
              <GraphPanel
                title="Relationship Graph"
                graph={debugRelationshipGraph}
                emptyText="No debug relationship graph."
                showVisibility
              />
              <GraphPanel
                title="Faction Graph"
                graph={debugFactionGraph}
                emptyText="No debug faction graph."
                showVisibility
              />
            </section>
            <NPCSimulationDebugger
              summaries={npcSimulationSummaries}
              selectedNPCId={selectedSimulationNPCId}
              detail={npcSimulationDetail}
              events={npcSimulationEvents}
              dryRun={npcSimulationDryRun}
              behaviorTimeline={npcBehaviorTimeline}
              behaviorTimelineError={npcBehaviorTimelineError}
              behaviorTurnFrom={npcBehaviorTurnFrom}
              behaviorTurnTo={npcBehaviorTurnTo}
              behaviorFilter={npcBehaviorFilter}
              error={npcSimulationError}
              onSelectNPC={(npcId) => void handleSelectSimulationNPC(npcId)}
              onRefresh={() => void refreshNPCSimulationDebugger()}
              onDryRun={() => void handleNPCSimulationDryRun()}
              onRefreshBehaviorTimeline={() => void refreshNPCBehaviorTimeline()}
              onBehaviorTurnFromChange={setNPCBehaviorTurnFrom}
              onBehaviorTurnToChange={setNPCBehaviorTurnTo}
              onBehaviorFilterChange={setNPCBehaviorFilter}
              disabled={!sessionId || isLoading}
            />
            <GameplayModuleDebugger
              modules={moduleDebugSummaries}
              selectedModuleId={selectedModuleDebugId}
              detail={moduleDebugDetail}
              dryRun={moduleDebugDryRun}
              error={moduleDebugError}
              onSelectModule={(moduleId) => void handleSelectGameplayModule(moduleId)}
              onRefresh={() => void refreshGameplayModuleDebugger()}
              onDryRun={(actionId) => void handleGameplayModuleDryRun(actionId)}
              disabled={isLoading}
            />
            <VisibleDebugStateCompare
              visibleState={visibleState}
              events={timeline}
              saves={saves}
              modules={moduleDebugSummaries}
              lastResponse={lastResponse}
            />
            <StateDeltaViewerPanel events={timeline} />
            <CrashReportViewer
              reports={crashReports}
              selectedReportId={selectedCrashReportId}
              selectedReport={selectedCrashReport}
              error={crashReportError}
              onRefresh={() => void refreshCrashReports()}
              onSelect={(reportId) => void handleSelectCrashReport(reportId)}
              onDelete={(reportId) => void handleDeleteCrashReport(reportId)}
            />
            <section className="debug-group">
              <h2>Social Consequences</h2>
              <DebugEventSummary events={socialDebugEvents} emptyText="No social events." />
            </section>
            <section className="debug-group">
              <h2>Combat / Injury</h2>
              <DebugEventSummary events={combatDebugEvents} emptyText="No combat events." />
            </section>
            <section className="debug-group">
              <h2>Raw Reputation</h2>
              {rawReputationDeltas.length === 0 ? (
                <p className="muted">No reputation deltas.</p>
              ) : (
                <pre>{JSON.stringify(rawReputationDeltas, null, 2)}</pre>
              )}
            </section>
            <section className="debug-group">
              <h2>Debug Snapshot</h2>
              <pre>{JSON.stringify({ visibleState, saves, lastResponse }, null, 2)}</pre>
            </section>
            </DebugGate>
          </div>
        )}
      </aside>
    </main>
  );
}

function StudioHome({
  status,
  selectedProjectId,
  configSummary,
  localConfigSummary,
  localConfigIssues,
  localEnvTemplate,
  localUpdateNotes,
  desktopHealth,
  localStudioStatus,
  localStudioConfig,
  localStudioStartupChecks,
  localStudioError,
  backupPlan,
  backupResult,
  restorePlan,
  backupRestoreError,
  recoveryIssues,
  recoveryPlan,
  recoveryError,
  localLogs,
  localLogsError,
  diagnosticsBundlePreview,
  diagnosticsBundleCreateResult,
  diagnosticsBundleError,
  workspaces,
  workspaceTemplates,
  recentProjects,
  currentWorkspaceId,
  saves,
  narrativeEvalReports,
  selectedNarrativeEval,
  performanceRecent,
  performanceSummary,
  playtestReports,
  selectedPlaytest,
  playtestBatchReport,
  scenarioRegressionCases,
  scenarioRegressionRuns,
  selectedScenarioRegressionRun,
  worldHealth,
  contentCoverage,
  error,
  workspaceError,
  workspaceMessage,
  configError,
  updateNotesError,
  desktopHealthError,
  narrativeEvalError,
  performanceError,
  playtestError,
  scenarioRegressionError,
  worldHealthError,
  contentCoverageError,
  onRefresh,
  onRunNarrativeEval,
  onSelectNarrativeEval,
  onRefreshPerformance,
  onRunPlaytest,
  onRunPlaytestBatch,
  onSelectPlaytest,
  onRefreshPlaytests,
  onRunScenarioRegression,
  onSelectScenarioRegression,
  onRefreshScenarioRegressions,
  onRunWorldHealth,
  onRefreshWorldHealth,
  onRunContentCoverage,
  onRefreshContentCoverage,
  onAddWorkspace,
  onCreateWorkspaceFromTemplate,
  onSelectWorkspace,
  onRemoveRecentProject,
  onClearRecentProjects,
  onRefreshLocalConfig,
  onGenerateLocalEnvTemplate,
  onRefreshUpdateNotes,
  onRunDesktopHealthCheck,
  onRefreshLocalStudio,
  onBackupDryRun,
  onCreateBackup,
  onRestoreDryRun,
  onRefreshRecovery,
  onDryRunRecovery,
  onRefreshLocalLogs,
  onPreviewDiagnosticsBundle,
  onPreviewDiagnosticsBundleWithOptions,
  onCreateDiagnosticsBundle,
  onSelectPromptProfile,
  onNavigate
}: {
  status: StudioStatus | null;
  selectedProjectId: string;
  configSummary: StudioConfigSummary | null;
  localConfigSummary: LocalConfigSummary | null;
  localConfigIssues: LocalConfigIssue[];
  localEnvTemplate: LocalEnvTemplateResponse | null;
  localUpdateNotes: LocalUpdateNotesIndex | null;
  desktopHealth: DesktopHealthCheckReport | null;
  localStudioStatus: LocalStudioStatus | null;
  localStudioConfig: LocalStudioConfigSummary | null;
  localStudioStartupChecks: LocalStudioStartupChecks | null;
  localStudioError: string;
  backupPlan: BackupPlan | null;
  backupResult: BackupCreateResponse | null;
  restorePlan: RestorePlan | null;
  backupRestoreError: string;
  recoveryIssues: RecoveryIssue[];
  recoveryPlan: RecoveryPlan | null;
  recoveryError: string;
  localLogs: LocalLogListResponse | null;
  localLogsError: string;
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  diagnosticsBundleCreateResult: DiagnosticsBundleCreateResponse | null;
  diagnosticsBundleError: string;
  workspaces: ProjectWorkspace[];
  workspaceTemplates: WorkspaceTemplate[];
  recentProjects: RecentProjectEntry[];
  currentWorkspaceId: string;
  saves: SaveSummary[];
  narrativeEvalReports: NarrativeEvalReport[];
  selectedNarrativeEval: NarrativeEvalReport | null;
  performanceRecent: DebugPerformanceRecentResponse | null;
  performanceSummary: DebugPerformanceSummaryResponse | null;
  playtestReports: PlaytestReport[];
  selectedPlaytest: PlaytestReport | null;
  playtestBatchReport: PlaytestBatchRun | null;
  scenarioRegressionCases: ScenarioRegressionCase[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  selectedScenarioRegressionRun: ScenarioRegressionRun | null;
  worldHealth: WorldHealthScore | null;
  contentCoverage: ContentCoverageReport | null;
  error: string;
  workspaceError: string;
  workspaceMessage: string;
  configError: string;
  updateNotesError: string;
  desktopHealthError: string;
  narrativeEvalError: string;
  performanceError: string;
  playtestError: string;
  scenarioRegressionError: string;
  worldHealthError: string;
  contentCoverageError: string;
  onRefresh: () => void;
  onRunNarrativeEval: () => void;
  onSelectNarrativeEval: (runId: string) => void;
  onRefreshPerformance: () => void;
  onRunPlaytest: (options: {
    worldId: string;
    agentType: string;
    steps: number;
    seed: number;
    saveLoadCheck: boolean;
  }) => void;
  onRunPlaytestBatch: (options: {
    worldId: string;
    agentTypes: string[];
    seeds: number[];
    steps: number;
    stopOnBlocker: boolean;
    saveLoadCheck: boolean;
  }) => void;
  onSelectPlaytest: (runId: string) => void;
  onRefreshPlaytests: () => void;
  onRunScenarioRegression: (options: { worldId: string; scenarioIds: string[] }) => void;
  onSelectScenarioRegression: (runId: string) => void;
  onRefreshScenarioRegressions: () => void;
  onRunWorldHealth: () => void;
  onRefreshWorldHealth: () => void;
  onRunContentCoverage: () => void;
  onRefreshContentCoverage: () => void;
  onAddWorkspace: (path: string, name?: string) => void;
  onCreateWorkspaceFromTemplate: (templateId: WorkspaceTemplateType, path: string, name?: string) => void;
  onSelectWorkspace: (workspaceId: string) => void;
  onRemoveRecentProject: (workspaceId: string) => void;
  onClearRecentProjects: () => void;
  onRefreshLocalConfig: () => void;
  onGenerateLocalEnvTemplate: () => void;
  onRefreshUpdateNotes: () => void;
  onRunDesktopHealthCheck: () => void;
  onRefreshLocalStudio: () => void;
  onBackupDryRun: () => void;
  onCreateBackup: () => void;
  onRestoreDryRun: (backupPath: string, targetProjectId: string) => void;
  onRefreshRecovery: () => void;
  onDryRunRecovery: () => void;
  onRefreshLocalLogs: () => void;
  onPreviewDiagnosticsBundle: () => void;
  onPreviewDiagnosticsBundleWithOptions: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
  onCreateDiagnosticsBundle: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
  onSelectPromptProfile: (profileId: string) => void;
  onNavigate: (mode: AppMode, toolId?: AuthoringToolId) => void;
}) {
  const recentSaves = status?.recent_saves.length ? status.recent_saves : saves.slice(0, 5);
  const validationSummaries = status?.validation_summaries ?? [];
  const unhealthyWorlds = validationSummaries.filter((item) => !item.ok).length;
  const [workspacePath, setWorkspacePath] = useState<string>("");
  const [workspaceName, setWorkspaceName] = useState<string>("");

  return (
    <section className="studio-home">
      <PageHeader
        eyebrow="Local Studio"
        title="Project Dashboard"
        description="Safe status for local worlds, saves, validation, providers, and studio tools."
        actions={<button type="button" onClick={onRefresh}>Refresh</button>}
      />

      <ErrorPanel message={error} />
      <LocalStatusBar
        projectLoaded={Boolean(selectedProjectId || currentWorkspaceId)}
        backendStatus={status?.backend_status ?? "unavailable"}
        providerStatus={configSummary?.provider_status ?? status?.local_model_provider_status ?? "unknown"}
        qualityStatus={worldHealth ? "available" : "not run"}
        debugEnabled={status?.debug_api_enabled ?? false}
        apiKeyConfigured={configSummary?.api_key_configured ?? localConfigSummary?.api_key_configured}
      />
      <LocalLauncherStatusPanel
        status={localStudioStatus}
        config={localStudioConfig}
        startupChecks={localStudioStartupChecks}
        error={localStudioError}
        onRefresh={onRefreshLocalStudio}
        onNavigate={onNavigate}
      />
      <ProjectHomeRedesignPanel
        status={status}
        selectedProjectId={selectedProjectId}
        configSummary={configSummary}
        worldHealth={worldHealth}
        recentSaves={recentSaves}
        validationSummaries={validationSummaries}
        onNavigate={onNavigate}
      />
      <LocalHelpOnboardingPanel />
      <QualityDashboardUXPanel
        worldHealth={worldHealth}
        narrativeEvalReports={narrativeEvalReports}
        playtestReports={playtestReports}
        scenarioRegressionRuns={scenarioRegressionRuns}
        contentCoverage={contentCoverage}
      />
      <UnifiedQualityGateDashboard
        worldHealth={worldHealth}
        narrativeEvalReports={narrativeEvalReports}
        playtestReports={playtestReports}
        scenarioRegressionRuns={scenarioRegressionRuns}
        contentCoverage={contentCoverage}
        diagnosticsBundlePreview={diagnosticsBundlePreview}
        backupPlan={backupPlan}
        configSummary={configSummary}
        localConfigIssues={localConfigIssues}
        onRunWorld={onRunWorldHealth}
        onRunNovel={onRunNarrativeEval}
        onRunPlaytest={() =>
          onRunPlaytest({
            worldId: "mist_valley",
            agentType: "random_valid_action_agent",
            steps: 12,
            seed: 123,
            saveLoadCheck: true
          })
        }
        onRunDiagnostics={onPreviewDiagnosticsBundle}
      />
      <DiagnosticsExportPanel
        selectedProjectId={selectedProjectId}
        status={status}
        configSummary={configSummary}
        localConfigSummary={localConfigSummary}
        worldHealth={worldHealth}
        desktopHealth={desktopHealth}
        safeErrors={[error, configError, desktopHealthError, worldHealthError].filter(Boolean)}
      />
      <DiagnosticsBundlePanel
        preview={diagnosticsBundlePreview}
        createResult={diagnosticsBundleCreateResult}
        error={diagnosticsBundleError}
        debugEnabled={status?.debug_api_enabled ?? false}
        onPreview={onPreviewDiagnosticsBundleWithOptions}
        onCreate={onCreateDiagnosticsBundle}
      />
      <LocalTestRunDashboard
        diagnosticsBundlePreview={diagnosticsBundlePreview}
        worldHealth={worldHealth}
        narrativeEvalReports={narrativeEvalReports}
        playtestReports={playtestReports}
        scenarioRegressionRuns={scenarioRegressionRuns}
        performanceSummary={performanceSummary}
        contentCoverage={contentCoverage}
      />
      <SafeDebugExportWizard
        debugEnabled={status?.debug_api_enabled ?? false}
        diagnosticsPreview={diagnosticsBundlePreview}
        diagnosticsCreateResult={diagnosticsBundleCreateResult}
        error={diagnosticsBundleError}
        onPreview={onPreviewDiagnosticsBundleWithOptions}
        onCreate={onCreateDiagnosticsBundle}
      />
      <ProjectSelectorPanel
        workspaces={workspaces}
        templates={workspaceTemplates}
        currentWorkspaceId={currentWorkspaceId}
        pathValue={workspacePath}
        nameValue={workspaceName}
        error={workspaceError}
        message={workspaceMessage}
        onPathChange={setWorkspacePath}
        onNameChange={setWorkspaceName}
        onSelect={onSelectWorkspace}
        onAdd={() => {
          onAddWorkspace(workspacePath, workspaceName || undefined);
          setWorkspacePath("");
          setWorkspaceName("");
        }}
        onCreateFromTemplate={(templateId, path, name) => {
          onCreateWorkspaceFromTemplate(templateId, path, name);
          setWorkspacePath("");
          setWorkspaceName("");
        }}
      />
      <RecentProjectsPanel
        projects={recentProjects}
        onOpen={onSelectWorkspace}
        onRemove={onRemoveRecentProject}
        onClear={onClearRecentProjects}
      />
      <LocalConfigWizardPanel
        summary={localStudioConfig}
        startupChecks={localStudioStartupChecks}
        error={localStudioError || configError}
        onRefresh={onRefreshLocalStudio}
        onOpenProviders={() => onNavigate("prompt_lab")}
      />
      <BackupRestoreWizardPanel
        plan={backupPlan}
        result={backupResult}
        restorePlan={restorePlan}
        error={backupRestoreError}
        onDryRun={onBackupDryRun}
        onCreate={onCreateBackup}
        onRestoreDryRun={onRestoreDryRun}
      />
      <ErrorRecoveryWizardPanel
        issues={recoveryIssues}
        plan={recoveryPlan}
        error={recoveryError}
        onRefresh={onRefreshRecovery}
        onDryRun={onDryRunRecovery}
      />
      <LocalLogViewerPanel
        logs={localLogs}
        error={localLogsError}
        debugEnabled={status?.debug_api_enabled ?? false}
        onRefresh={onRefreshLocalLogs}
      />

      <div className="studio-grid">
        <DashboardCard title="Backend" value={status?.backend_status ?? "unavailable"}>
          <p>Engine {status?.engine_version ?? "unknown"}</p>
          <p>Schema {status?.schema_version ?? "unknown"}</p>
        </DashboardCard>
        <DashboardCard title="Worlds" value={String(status?.worlds_count ?? 0)}>
          <p>{unhealthyWorlds ? `${unhealthyWorlds} need attention` : "Validation clean or unavailable"}</p>
        </DashboardCard>
        <DashboardCard title="LLM Provider" value={status?.llm_provider ?? "unknown"}>
          <p>{status?.local_model_provider_status ?? "No local model status"}</p>
        </DashboardCard>
        <DashboardCard title="Local APIs" value="Status">
          <StatusDot label="Authoring" enabled={status?.authoring_api_enabled} />
          <StatusDot label="Debug" enabled={status?.debug_api_enabled} />
          <StatusDot label="Performance" enabled={status?.performance_logging_enabled} />
        </DashboardCard>
      </div>

      <div className="studio-columns">
        <section className="studio-section">
          <h3>Recent Saves</h3>
          {recentSaves.length ? (
            <ul className="compact-list">
              {recentSaves.map((save) => (
                <li key={save.save_id}>
                  <strong>{save.world_name}</strong> turn {save.turn}, {save.current_location_name}
                  <span className="muted"> 路 {save.formatted_time}</span>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No saves yet." detail="Start or save a local session to populate this list." />
          )}
        </section>

        <section className="studio-section">
          <h3>Validation</h3>
          {validationSummaries.length ? (
            <ul className="compact-list">
              {validationSummaries.map((summary) => (
                <li key={summary.world_id}>
                  <strong>{summary.world_id}</strong>{" "}
                  {summary.ok ? "ok" : `${summary.error_count} errors`}
                  {summary.warning_count > 0 && `, ${summary.warning_count} warnings`}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No validation summary." detail="Run world validation from Authoring to see local results here." />
          )}
        </section>

        <section className="studio-section">
          <h3>Playtests</h3>
          {status?.playtest_summary.available ? (
            <p className="muted">
              Recent runs: {status.playtest_summary.recent_runs}
              {status.playtest_summary.latest_status
                ? ` 路 ${status.playtest_summary.latest_status}`
                : ""}
            </p>
          ) : (
            <EmptyState title="No playtest summary." detail="Run deterministic playtests from the local tools when needed." />
          )}
        </section>
      </div>

      <section className="studio-section">
        <h3>Quick Actions</h3>
        <div className="quick-actions">
          <button type="button" onClick={() => onNavigate("play")}>
            Play
          </button>
          <button type="button" onClick={() => onNavigate("authoring")}>
            Authoring
          </button>
          <button type="button" onClick={() => onNavigate("play")}>
            Save Browser
          </button>
          <button type="button" onClick={() => onNavigate("play")}>
            Migration
          </button>
          <button type="button" onClick={() => onNavigate("authoring")}>
            Mod Manager
          </button>
          <button type="button" onClick={() => onNavigate("play")}>
            Graphs
          </button>
          <button type="button" onClick={() => onNavigate("studio")}>
            Narrative Evals
          </button>
          <button type="button" onClick={() => onNavigate("studio")}>
            Performance
          </button>
          <button type="button" onClick={() => onNavigate("studio")}>
            Settings
          </button>
        </div>
      </section>

      <WorldHealthDashboard
        health={worldHealth}
        error={worldHealthError}
        onRun={onRunWorldHealth}
        onRefresh={onRefreshWorldHealth}
      />

      <ContentCoverageDashboard
        report={contentCoverage}
        error={contentCoverageError}
        onRun={onRunContentCoverage}
        onRefresh={onRefreshContentCoverage}
        onOpenAuthoring={(toolId) => onNavigate("authoring", toolId)}
      />

      <NarrativeQualityDashboard
        reports={narrativeEvalReports}
        selectedReport={selectedNarrativeEval}
        error={narrativeEvalError}
        onRun={onRunNarrativeEval}
        onSelect={onSelectNarrativeEval}
      />

      <PerformanceDashboard
        recent={performanceRecent}
        summary={performanceSummary}
        error={performanceError}
        onRefresh={onRefreshPerformance}
      />

      <PlaytestingDashboard
        reports={playtestReports}
        selectedReport={selectedPlaytest}
        batchReport={playtestBatchReport}
        error={playtestError}
        onRun={onRunPlaytest}
        onRunBatch={onRunPlaytestBatch}
        onSelect={onSelectPlaytest}
        onRefresh={onRefreshPlaytests}
      />

      <ScenarioRegressionDashboard
        cases={scenarioRegressionCases}
        runs={scenarioRegressionRuns}
        selectedRun={selectedScenarioRegressionRun}
        error={scenarioRegressionError}
        onRun={onRunScenarioRegression}
        onSelect={onSelectScenarioRegression}
        onRefresh={onRefreshScenarioRegressions}
      />

      <SettingsPrivacyPanel
        selectedProjectId={selectedProjectId}
        summary={configSummary}
        localConfigSummary={localConfigSummary}
        localConfigIssues={localConfigIssues}
        localEnvTemplate={localEnvTemplate}
        currentWorkspace={workspaces.find((workspace) => workspace.workspace_id === currentWorkspaceId) ?? null}
        recentProjectCount={recentProjects.length}
        error={configError}
        onSelectPromptProfile={onSelectPromptProfile}
        onRefreshLocalConfig={onRefreshLocalConfig}
        onGenerateLocalEnvTemplate={onGenerateLocalEnvTemplate}
        onClearRecentProjects={onClearRecentProjects}
      />

      <DesktopHealthCheckPanel
        report={desktopHealth}
        error={desktopHealthError}
        onRun={onRunDesktopHealthCheck}
        onOpenRecovery={() => onNavigate("studio")}
      />

      <LocalUpdateNotesPanel
        index={localUpdateNotes}
        error={updateNotesError}
        onRefresh={onRefreshUpdateNotes}
      />

      <LocalOnlyNotice>
        Dashboard data is a safe local summary. It does not include API keys, raw GameState,
        raw state_deltas, or hidden narrative facts.
      </LocalOnlyNotice>
    </section>
  );
}

function WorldHealthDashboard({
  health,
  error,
  onRun,
  onRefresh
}: {
  health: WorldHealthScore | null;
  error: string;
  onRun: () => void;
  onRefresh: () => void;
}) {
  const blockers = health?.blockers ?? [];
  const warnings = health?.warnings ?? [];
  return (
    <section className="studio-section world-health-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>World Health</h3>
          <p className="muted">Local heuristic score from validation, quality reports, coverage, and benchmarks.</p>
        </div>
        <div className="quick-actions">
          <button type="button" onClick={onRefresh}>
            Refresh
          </button>
          <button type="button" onClick={onRun}>
            Run Health
          </button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Overall" value={health ? String(health.overall_score) : "none"}>
          <p>{health?.created_at ?? "Run health analysis to create a local report"}</p>
        </DashboardCard>
        <DashboardCard title="Blockers" value={String(blockers.length)}>
          <p>Release-impacting issues</p>
        </DashboardCard>
        <DashboardCard title="Warnings" value={String(warnings.length)}>
          <p>Non-blocking review items</p>
        </DashboardCard>
        <DashboardCard title="Sources" value={String(health?.source_report_ids.length ?? 0)}>
          <p>Quality and benchmark reports</p>
        </DashboardCard>
      </div>

      {health ? (
        <>
          <section>
            <h3>Category Scores</h3>
            <div className="perf-table">
              {health.category_scores.map((category) => (
                <div className="perf-row" key={category.dimension}>
                  <span>{category.dimension}</span>
                  <span>{category.score}/100</span>
                  <span>{category.status}</span>
                  <span>{category.explanation}</span>
                  <span className="perf-bar" style={{ "--bar-width": `${category.score}%` } as React.CSSProperties} />
                </div>
              ))}
            </div>
          </section>
          <div className="studio-columns">
            <section>
              <h3>Blockers</h3>
              <ItemList
                emptyText="No blocker issues reported."
                items={blockers.map((item) => <span key={item}>{redactReportText(item)}</span>)}
              />
            </section>
            <section>
              <h3>Recommended Actions</h3>
              <ItemList
                emptyText="No recommendations yet."
                items={health.recommended_actions.map((item) => <span key={item}>{redactReportText(item)}</span>)}
              />
            </section>
          </div>
        </>
      ) : (
        <EmptyState title="No world health report." detail="Run local health analysis to aggregate quality signals." />
      )}
    </section>
  );
}

function ContentCoverageDashboard({
  report,
  error,
  onRun,
  onRefresh,
  onOpenAuthoring
}: {
  report: ContentCoverageReport | null;
  error: string;
  onRun: () => void;
  onRefresh: () => void;
  onOpenAuthoring: (toolId?: AuthoringToolId) => void;
}) {
  const [showUncoveredOnly, setShowUncoveredOnly] = useState<boolean>(false);
  const [plan, setPlan] = useState<ContentCoveragePlan | null>(null);
  const [planError, setPlanError] = useState<string>("");
  const [isPlanning, setIsPlanning] = useState<boolean>(false);
  const rows = report ? contentCoverageRows(report) : [];
  const average = rows.length
    ? Math.round(rows.reduce((total, row) => total + row.summary.coverage_percent, 0) / rows.length)
    : 0;
  async function handlePlanCoverage() {
    if (!report || isPlanning) {
      return;
    }
    setIsPlanning(true);
    setPlanError("");
    try {
      const response = await planContentCoverage({
        target_world: report.world_id,
        genre: "general",
        desired_playtime: "short",
        desired_complexity: "medium",
        current_content_coverage_report: report
      });
      setPlan(response);
    } catch (err) {
      setPlan(null);
      setPlanError(toErrorMessage(err));
    } finally {
      setIsPlanning(false);
    }
  }
  return (
    <section className="studio-section content-coverage-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>Content Coverage</h3>
          <p className="muted">Safe local coverage summary from events, playtests, and scenario regression runs.</p>
        </div>
        <div className="quick-actions">
          <button type="button" onClick={onRefresh}>Refresh</button>
          <button type="button" onClick={onRun}>Run Coverage</button>
          <button type="button" onClick={handlePlanCoverage} disabled={!report || isPlanning}>
            {isPlanning ? "Planning..." : "Plan Coverage"}
          </button>
          <button type="button" onClick={() => onOpenAuthoring()}>Authoring</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      <ErrorPanel message={planError} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Average" value={report ? `${average}%` : "none"}>
          <p>{report ? report.world_id : "Run coverage to create a local report"}</p>
        </DashboardCard>
        <DashboardCard title="Locations" value={formatCoverage(report?.locations)}>
          <p>visited locations</p>
        </DashboardCard>
        <DashboardCard title="NPCs" value={formatCoverage(report?.npcs)}>
          <p>seen or talked to</p>
        </DashboardCard>
        <DashboardCard title="Quests" value={formatCoverage(report?.quests)}>
          <p>triggered stages</p>
        </DashboardCard>
      </div>
      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={showUncoveredOnly}
          onChange={(event) => setShowUncoveredOnly(event.target.checked)}
        />
        Show uncovered only
      </label>
      {report ? (
        <div className="perf-table">
          {rows.map((row) => (
            <div className="perf-row" key={row.label}>
              <span>{row.label}</span>
              <span>{row.summary.coverage_percent}%</span>
              <span>{row.summary.covered}/{row.summary.total}</span>
              <span>
                {showUncoveredOnly
                  ? safeIdList(row.summary.uncovered_ids)
                  : row.summary.safe_summary}
              </span>
              <span className="perf-bar" style={{ "--bar-width": `${row.summary.coverage_percent}%` } as React.CSSProperties} />
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No content coverage report." detail="Run coverage after playtests or scenario regression." />
      )}
      {report && (
        <p className="muted">
          Hidden content is redacted from normal coverage details. Redacted counts:{" "}
          {Object.entries(report.hidden_entities_redacted)
            .map(([key, value]) => `${key} ${value}`)
            .join(", ")}
        </p>
      )}
      {plan && (
        <section className="studio-section nested-section">
          <div className="mod-detail-header">
            <div>
              <h4>Coverage Plan</h4>
              <p className="muted">Rule-based planning suggestions only; no content is generated or saved.</p>
            </div>
          </div>
          <div className="studio-grid compact-dashboard-grid">
            {contentCoveragePlanGroups(plan).map((group) => (
              <DashboardCard title={group.label} value={String(group.items.length)} key={group.label}>
                {group.items.length ? (
                  <ul className="compact-list">
                    {group.items.map((item) => (
                      <li key={`${group.label}-${item.summary}`}>
                        <strong>{item.priority}</strong> {item.summary}
                        {item.safe_refs.length > 0 && (
                          <span className="muted"> refs: {item.safe_refs.join(", ")}</span>
                        )}
                        <button
                          type="button"
                          onClick={() => onOpenAuthoring(coveragePlannerTool(item.recommended_tool))}
                        >
                          Open Tool
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No suggested gaps.</p>
                )}
              </DashboardCard>
            ))}
          </div>
        </section>
      )}
    </section>
  );
}

function contentCoveragePlanGroups(plan: ContentCoveragePlan) {
  return [
    { label: "Locations", items: plan.missing_location_types },
    { label: "NPCs", items: plan.missing_npc_archetypes },
    { label: "Quests", items: plan.missing_quest_types },
    { label: "Clues", items: plan.missing_clue_paths },
    { label: "Factions", items: plan.missing_faction_hooks },
    { label: "RP Scenes", items: plan.missing_rp_scenes },
    { label: "Scenarios", items: plan.missing_scenario_regressions },
    { label: "Playtests", items: plan.missing_playtest_paths }
  ];
}

function coveragePlannerTool(tool: string): AuthoringToolId {
  const mapping: Record<string, AuthoringToolId> = {
    location_clusters: "location_clusters",
    npc_pack_generator: "npc_pack_generator",
    quest_pack_generator: "quest_pack_generator",
    mystery_templates: "quest_pack_generator",
    faction_templates: "social",
    dialogue_scenes: "dialogue_scenes",
    scenarios: "scenarios",
    playtests: "scenarios"
  };
  return mapping[tool] ?? "project_dashboard";
}

function contentCoverageRows(report: ContentCoverageReport) {
  return [
    { label: "Locations", summary: report.locations },
    { label: "NPCs", summary: report.npcs },
    { label: "Items", summary: report.items },
    { label: "Quests", summary: report.quests },
    { label: "Facts", summary: report.facts },
    { label: "Factions", summary: report.factions },
    { label: "Rumors", summary: report.rumors },
    { label: "Crimes", summary: report.crimes },
    { label: "Combat", summary: report.combat_encounters },
    { label: "Shops / Trade", summary: report.shops_trade }
  ];
}

function formatCoverage(summary?: { covered: number; total: number } | null): string {
  if (!summary) {
    return "none";
  }
  return `${summary.covered}/${summary.total}`;
}

function safeIdList(ids: string[]): string {
  return ids.length ? ids.slice(0, 8).join(", ") : "none";
}

function NarrativeQualityDashboard({
  reports,
  selectedReport,
  error,
  onRun,
  onSelect
}: {
  reports: NarrativeEvalReport[];
  selectedReport: NarrativeEvalReport | null;
  error: string;
  onRun: () => void;
  onSelect: (runId: string) => void;
}) {
  const passRate = selectedReport?.total_cases
    ? Math.round((selectedReport.passed / selectedReport.total_cases) * 100)
    : 0;
  const failedCases = selectedReport?.case_results.filter((item) => !item.passed && !item.skipped) ?? [];

  return (
    <section className="studio-section narrative-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>Narrative Quality</h3>
          <p className="muted">Deterministic local evals. No external LLM judge is used.</p>
        </div>
        <button type="button" onClick={onRun}>
          Run Evals
        </button>
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Pass rate" value={`${passRate}%`}>
          <p>{selectedReport ? `${selectedReport.passed}/${selectedReport.total_cases} passed` : "No run yet"}</p>
        </DashboardCard>
        <DashboardCard title="Failed" value={String(selectedReport?.failed ?? 0)}>
          <p>{selectedReport?.skipped ?? 0} skipped</p>
        </DashboardCard>
        <DashboardCard title="Latest run" value={selectedReport ? shortRunId(selectedReport.run_id) : "none"}>
          <p>{selectedReport?.created_at ?? "Run evals to create a report"}</p>
        </DashboardCard>
        <DashboardCard title="History" value={String(reports.length)}>
          <p>Local in-memory reports</p>
        </DashboardCard>
      </div>

      {reports.length > 0 && (
        <label>
          Run history
          <select
            value={selectedReport?.run_id ?? ""}
            onChange={(event) => onSelect(event.target.value)}
          >
            {reports.map((report) => (
              <option key={report.run_id} value={report.run_id}>
                {shortRunId(report.run_id)} 路 {report.passed}/{report.total_cases}
              </option>
            ))}
          </select>
        </label>
      )}

      {selectedReport && (
        <div className="studio-columns">
          <section>
            <h3>Categories</h3>
            <ul className="compact-list">
              {Object.entries(selectedReport.categories).map(([category, counts]) => (
                <li key={category}>
                  <strong>{category}</strong>: {counts.passed ?? 0} passed, {counts.failed ?? 0} failed
                </li>
              ))}
            </ul>
          </section>
          <section>
            <h3>Failed Cases</h3>
            {failedCases.length ? (
              <ul className="compact-list">
                {failedCases.map((item) => (
                  <li key={item.case_id}>
                    <strong>{item.case_id}</strong> <span className="badge">{item.category}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="No failed cases." />
            )}
          </section>
          <section>
            <h3>Failure Reasons</h3>
            {failedCases.length ? (
              <ul className="compact-list">
                {failedCases.flatMap((item) =>
                  item.failure_reasons.map((reason) => (
                    <li key={`${item.case_id}-${reason}`}>
                      {item.case_id}: {redactEvalReason(reason)}
                    </li>
                  ))
                )}
              </ul>
            ) : (
              <EmptyState title="No failure reasons." />
            )}
          </section>
        </div>
      )}
    </section>
  );
}

function shortRunId(runId: string): string {
  return runId.slice(0, 8);
}

function redactEvalReason(reason: string): string {
  return reason.replace(/forbidden:.+$/i, "forbidden:[redacted]");
}

function redactReportText(value: string): string {
  return redactAuthoringPreviewText(value)
    .replace(/hidden_fact_text_visible:[^\s,;]+/g, "hidden_fact_text_visible:[redacted]")
    .replace(/(hidden[_\s-]?truth|hidden[_\s-]?witness|npc[_\s-]?knowledge|private[_\s-]?notes?)\s*[:=]\s*[^,;\n]+/gi, "$1=[redacted]");
}

function parseCsvList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function parseSeedList(value: string): number[] {
  const seeds = parseCsvList(value)
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item));
  return seeds.length ? seeds : [123];
}

function PerformanceDashboard({
  recent,
  summary,
  error,
  onRefresh
}: {
  recent: DebugPerformanceRecentResponse | null;
  summary: DebugPerformanceSummaryResponse | null;
  error: string;
  onRefresh: () => void;
}) {
  const [range, setRange] = useState<"all" | "hour" | "day">("all");
  const entries = summary?.entries ?? [];
  const samples = useMemo(() => filterPerformanceSamplesByRange(recent?.samples ?? [], range), [range, recent]);
  const proRows = useMemo(() => buildPerformanceProRows(entries, samples), [entries, samples]);
  const maxDuration = Math.max(1, ...entries.map((entry) => entry.max_duration_ms));
  const trackedStages = [
    "intent_parse",
    "action_resolve",
    "world_tick",
    "narrator",
    "save/load",
    "memory search",
    "authoring.validation"
  ];

  return (
    <section className="studio-section performance-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>Performance Dashboard Pro</h3>
          <p className="muted">Local samples only. Prompt text, output text, hidden facts, and API keys are not recorded or displayed.</p>
        </div>
        <button type="button" onClick={onRefresh}>
          Refresh Performance
        </button>
      </div>
      <ErrorPanel message={error} compact />
      <FilterToolbar>
        <label>
          Time range
          <select value={range} onChange={(event) => setRange(event.target.value as "all" | "hour" | "day")}>
            <option value="all">All loaded</option>
            <option value="hour">Last hour</option>
            <option value="day">Last day</option>
          </select>
        </label>
      </FilterToolbar>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Logging" value={summary?.enabled ? "enabled" : "disabled"}>
          <p>{summary ? `${summary.sample_count} samples` : "Debug API unavailable"}</p>
        </DashboardCard>
        <DashboardCard title="Game loop" value={formatDuration(findPerfEntry(entries, "game_loop.step")?.average_duration_ms)}>
          <p>total duration average</p>
        </DashboardCard>
        <DashboardCard title="Authoring validation" value={formatDuration(findPerfEntry(entries, "authoring.validation")?.average_duration_ms)}>
          <p>validation average</p>
        </DashboardCard>
        <DashboardCard title="Slowest" value={formatDuration(entries[0] ? Math.max(...entries.map((entry) => entry.max_duration_ms)) : undefined)}>
          <p>max observed sample</p>
        </DashboardCard>
      </div>

      <section>
        <h3>Performance Overview</h3>
        <div className="mode-landing-grid">
          {proRows.map((row) => (
            <section className="feature-card" key={row.category}>
              <div>
                <h4>{row.category}</h4>
                <p className="muted">{row.detail}</p>
              </div>
              <dl className="event-details">
                <dt>Average</dt>
                <dd>{formatDuration(row.averageMs)}</dd>
                <dt>Max</dt>
                <dd>{formatDuration(row.maxMs)}</dd>
                <dt>Samples</dt>
                <dd>{row.sampleCount}</dd>
              </dl>
            </section>
          ))}
        </div>
      </section>

      <section>
        <h3>Summary</h3>
        {entries.length ? (
          <div className="perf-table">
            {entries.map((entry) => (
              <div className="perf-row" key={entry.name}>
                <span>{entry.name}</span>
                <span>{entry.count} samples</span>
                <span>{formatDuration(entry.average_duration_ms)} avg</span>
                <span>{formatDuration(entry.max_duration_ms)} max</span>
                <span className="perf-bar" style={{ "--bar-width": `${Math.min(100, (entry.max_duration_ms / maxDuration) * 100)}%` } as React.CSSProperties} />
              </div>
            ))}
          </div>
        ) : (
          <EmptyState title="No performance samples." detail="Enable debug/perf APIs locally to inspect timing data." />
        )}
      </section>

      <section>
        <h3>Tracked Stages</h3>
        <div className="quick-actions">
          {trackedStages.map((stage) => (
            <span className="badge" key={stage}>{stage}</span>
          ))}
        </div>
      </section>

      <section>
        <h3>Recent Samples</h3>
        {samples.length ? (
          <ul className="compact-list">
            {samples.slice(-8).reverse().map((sample) => (
              <li key={sample.sample_id}>
                <strong>{sample.name}</strong> {formatDuration(sample.duration_ms)}
                {Object.keys(sample.stage_durations_ms).length > 0 && (
                  <span className="muted"> 路 {formatStageDurations(sample.stage_durations_ms)}</span>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No recent samples." />
        )}
      </section>
    </section>
  );
}

type PerformanceProRow = {
  category: string;
  averageMs?: number;
  maxMs?: number;
  sampleCount: number;
  detail: string;
};

function filterPerformanceSamplesByRange(samples: DebugPerformanceSample[], range: "all" | "hour" | "day"): DebugPerformanceSample[] {
  if (range === "all") {
    return samples;
  }
  const cutoff = Date.now() - (range === "hour" ? 60 * 60 * 1000 : 24 * 60 * 60 * 1000);
  return samples.filter((sample) => {
    const startedAt = Date.parse(sample.started_at);
    return Number.isFinite(startedAt) && startedAt >= cutoff;
  });
}

function buildPerformanceProRows(
  entries: DebugPerformanceSummaryResponse["entries"],
  samples: DebugPerformanceSample[]
): PerformanceProRow[] {
  return [
    performanceRow("backend API duration", entries, samples, ["api", "request", "game_loop.step"], "Local backend request and game-loop timing."),
    performanceRow("save/load duration", entries, samples, ["save", "load", "migration"], "Save/load and migration timing summaries."),
    {
      category: "event log size",
      averageMs: undefined,
      maxMs: undefined,
      sampleCount: samples.reduce((total, sample) => total + Number(sample.tags.event_count ?? 0), 0),
      detail: "EventLog size is shown as loaded sample event-count metadata when available.",
    },
    performanceRow("timeline replay duration", entries, samples, ["timeline", "replay"], "Timeline replay and debug replay timing."),
    performanceRow("provider call duration", entries, samples, ["provider", "llm", "narrator", "intent_parse"], "Provider Gateway timing only; prompts and outputs are not shown."),
    performanceRow("quality gate duration", entries, samples, ["quality", "eval", "validation"], "Quality, eval, and validation timing."),
    performanceRow("playtest duration", entries, samples, ["playtest", "scenario"], "Local automated playtest and scenario regression timing."),
    {
      category: "frontend build/chunk warning summary",
      averageMs: undefined,
      maxMs: undefined,
      sampleCount: 1,
      detail: "Latest build reports a Vite chunk-size warning; no source maps, prompts, secrets, or hidden data are displayed.",
    },
  ];
}

function performanceRow(
  category: string,
  entries: DebugPerformanceSummaryResponse["entries"],
  samples: DebugPerformanceSample[],
  tokens: string[],
  detail: string
): PerformanceProRow {
  const matchingEntries = entries.filter((entry) => tokens.some((token) => entry.name.toLowerCase().includes(token)));
  const matchingSamples = samples.filter((sample) => tokens.some((token) => sample.name.toLowerCase().includes(token) || Object.keys(sample.tags).some((tag) => tag.toLowerCase().includes(token))));
  const count = matchingEntries.reduce((total, entry) => total + entry.count, 0) || matchingSamples.length;
  const averageMs = matchingEntries.length
    ? matchingEntries.reduce((total, entry) => total + entry.average_duration_ms, 0) / matchingEntries.length
    : matchingSamples.length
      ? matchingSamples.reduce((total, sample) => total + sample.duration_ms, 0) / matchingSamples.length
      : undefined;
  const maxMs = matchingEntries.length
    ? Math.max(...matchingEntries.map((entry) => entry.max_duration_ms))
    : matchingSamples.length
      ? Math.max(...matchingSamples.map((sample) => sample.duration_ms))
      : undefined;
  return { category, averageMs, maxMs, sampleCount: count, detail };
}

function findPerfEntry(entries: DebugPerformanceSummaryResponse["entries"], name: string) {
  return entries.find((entry) => entry.name === name);
}

function PlaytestingDashboard({
  reports,
  selectedReport,
  batchReport,
  error,
  onRun,
  onRunBatch,
  onSelect,
  onRefresh
}: {
  reports: PlaytestReport[];
  selectedReport: PlaytestReport | null;
  batchReport: PlaytestBatchRun | null;
  error: string;
  onRun: (options: {
    worldId: string;
    agentType: string;
    steps: number;
    seed: number;
    saveLoadCheck: boolean;
  }) => void;
  onRunBatch: (options: {
    worldId: string;
    agentTypes: string[];
    seeds: number[];
    steps: number;
    stopOnBlocker: boolean;
    saveLoadCheck: boolean;
  }) => void;
  onSelect: (runId: string) => void;
  onRefresh: () => void;
}) {
  const [worldId, setWorldId] = useState<string>("mist_valley");
  const [agentType, setAgentType] = useState<string>("random_valid_action_agent");
  const [steps, setSteps] = useState<number>(12);
  const [seed, setSeed] = useState<number>(123);
  const [batchSeeds, setBatchSeeds] = useState<string>("1,2,3");
  const [batchAgents, setBatchAgents] = useState<string>("random_valid_action_agent,explore_agent");
  const [stopOnBlocker, setStopOnBlocker] = useState<boolean>(true);
  const [saveLoadCheck, setSaveLoadCheck] = useState<boolean>(true);
  const playtestSuites = useMemo(
    () => [
      {
        id: "world_action_path",
        title: "World action path",
        detail: "Single deterministic world path through GameLoop.",
        run: () => onRun({ worldId, agentType, steps, seed, saveLoadCheck })
      },
      {
        id: "scenario_tests",
        title: "Scenario tests",
        detail: "Batch-safe scenario-style probes using deterministic seeds.",
        run: () => onRunBatch({ worldId, agentTypes: ["quest_following_agent"], seeds: parseSeedList(batchSeeds), steps, stopOnBlocker, saveLoadCheck })
      },
      {
        id: "module_playtests",
        title: "Module playtests",
        detail: "Stress module actions through local playtest agents; no module code execution.",
        run: () => onRunBatch({ worldId, agentTypes: ["stress_agent"], seeds: parseSeedList(batchSeeds), steps, stopOnBlocker, saveLoadCheck })
      },
      {
        id: "regression_packs",
        title: "Regression packs",
        detail: "Multi-agent regression pack over local temporary runs.",
        run: () => onRunBatch({ worldId, agentTypes: parseCsvList(batchAgents), seeds: parseSeedList(batchSeeds), steps, stopOnBlocker, saveLoadCheck })
      }
    ],
    [agentType, batchAgents, batchSeeds, onRun, onRunBatch, saveLoadCheck, seed, steps, stopOnBlocker, worldId]
  );
  const issueCount = selectedReport
    ? selectedReport.errors.length +
      selectedReport.invariant_violations.length +
      selectedReport.visibility_leaks.length +
      selectedReport.save_load_failures.length
    : 0;
  const failedStep = selectedReport ? firstFailedPlaytestStep(selectedReport) : null;
  const actionCoverage = selectedReport ? new Set(selectedReport.actions_taken.map((action) => action.action_type)).size : 0;
  const eventCoverage = selectedReport?.final_state_summary.event_count ?? 0;

  return (
    <section className="studio-section playtesting-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>Automated Playtesting</h3>
          <p className="muted">Deterministic local agents. They act through the game loop and are not player AI.</p>
        </div>
        <button type="button" onClick={onRefresh}>
          Refresh Runs
        </button>
      </div>
      <ErrorPanel message={error} compact />
      {error.toLowerCase().includes("disabled") && (
        <div className="notice api-disabled-notice">
          Playtest API is disabled. Enable <code>ENABLE_PLAYTEST_API=true</code> or local debug API.
        </div>
      )}
      <section className="studio-section">
        <h3>Playtest Dashboard Pro</h3>
        <p className="muted">
          Local deterministic suites only. Reports are not uploaded, do not call real providers, and do not write real saves.
        </p>
        <div className="studio-grid compact-dashboard-grid">
          {playtestSuites.map((suite) => (
            <FeatureCard
              key={suite.id}
              title={suite.title}
              detail={suite.detail}
              action={<button type="button" onClick={suite.run}>Run Suite</button>}
            />
          ))}
        </div>
      </section>
      <div className="playtest-controls">
        <label>
          World
          <select value={worldId} onChange={(event) => setWorldId(event.target.value)}>
            {WORLD_OPTIONS.map((world) => (
              <option key={world.id} value={world.id}>{world.name}</option>
            ))}
          </select>
        </label>
        <label>
          Agent
          <select value={agentType} onChange={(event) => setAgentType(event.target.value)}>
            <option value="random_valid_action_agent">Random valid action</option>
            <option value="explore_agent">Explore</option>
            <option value="quest_following_agent">Quest following</option>
            <option value="stress_agent">Stress</option>
          </select>
        </label>
        <label>
          Steps
          <input type="number" min={0} max={250} value={steps} onChange={(event) => setSteps(Number(event.target.value))} />
        </label>
        <label>
          Seed
          <input type="number" value={seed} onChange={(event) => setSeed(Number(event.target.value))} />
        </label>
        <label className="checkbox-field">
          <input type="checkbox" checked={saveLoadCheck} onChange={(event) => setSaveLoadCheck(event.target.checked)} />
          Save/load check
        </label>
        <button type="button" onClick={() => onRun({ worldId, agentType, steps, seed, saveLoadCheck })}>
          Run Playtest
        </button>
      </div>

      <section className="studio-section">
        <h3>Batch Run</h3>
        <p className="muted">Runs multiple deterministic seeds and agents in serial with temporary saves only.</p>
        <div className="playtest-controls">
          <label>
            Agents
            <input value={batchAgents} onChange={(event) => setBatchAgents(event.target.value)} />
          </label>
          <label>
            Seeds
            <input value={batchSeeds} onChange={(event) => setBatchSeeds(event.target.value)} />
          </label>
          <label className="checkbox-field">
            <input type="checkbox" checked={stopOnBlocker} onChange={(event) => setStopOnBlocker(event.target.checked)} />
            Stop on blocker
          </label>
          <button
            type="button"
            onClick={() =>
              onRunBatch({
                worldId,
                agentTypes: parseCsvList(batchAgents),
                seeds: parseSeedList(batchSeeds),
                steps,
                stopOnBlocker,
                saveLoadCheck,
              })
            }
          >
            Run Batch
          </button>
        </div>
        {batchReport ? (
          <div className="studio-grid compact-dashboard-grid">
            <DashboardCard title="Batch Runs" value={String(batchReport.total_runs)}>
              <p>{shortRunId(batchReport.run_id)}</p>
            </DashboardCard>
            <DashboardCard title="Passed" value={String(batchReport.passed)}>
              <p>{batchReport.failed} failed</p>
            </DashboardCard>
            <DashboardCard title="Blockers" value={String(batchReport.blockers)}>
              <p>{batchReport.aggregate_issues.length} aggregate issues</p>
            </DashboardCard>
            <DashboardCard title="Avg Duration" value={`${Math.round(batchReport.performance_summary.average_duration_ms)}ms`}>
              <p>{batchReport.coverage_summary.seeds_run.join(", ") || "no seeds"}</p>
            </DashboardCard>
          </div>
        ) : (
          <EmptyState title="No batch report." detail="Run a batch to compare seeds and agents." />
        )}
        {batchReport && (
          <div className="studio-columns">
            <SectionCard title="Failed Items" description="Safe summaries only. Hidden content is redacted by the backend.">
              <ItemList
                emptyText="No failed batch items."
                items={batchReport.run_items
                  .filter((item) => !item.passed)
                  .map((item) => (
                    <span key={item.run_index}>
                      #{item.run_index} {item.agent_type} seed {item.seed}: {item.safe_failure_reasons.map(redactReportText).join("; ")}
                    </span>
                  ))}
              />
            </SectionCard>
            <SectionCard title="Coverage Summary" description="Aggregate action and location counts.">
              <ItemList
                emptyText="No coverage."
                items={Object.entries(batchReport.coverage_summary.action_types).map(([name, count]) => (
                  <span key={name}>{name}: {count}</span>
                ))}
              />
            </SectionCard>
          </div>
        )}
      </section>

      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Runs" value={String(reports.length)}>
          <p>local in-memory reports</p>
        </DashboardCard>
        <DashboardCard title="Turns" value={String(selectedReport?.turns_run ?? 0)}>
          <p>{selectedReport ? `${selectedReport.actions_taken.length} actions` : "No run selected"}</p>
        </DashboardCard>
        <DashboardCard title="Issues" value={String(issueCount)}>
          <p>errors, invariant, visibility, save/load</p>
        </DashboardCard>
        <DashboardCard title="Seed" value={String(selectedReport?.seed ?? seed)}>
          <p>{selectedReport?.agent_type ?? agentType}</p>
        </DashboardCard>
        <DashboardCard title="Result" value={selectedReport ? (issueCount ? "failed" : "passed") : "not run"}>
          <p>{failedStep ? `failed step ${failedStep.step}` : "safe summary only"}</p>
        </DashboardCard>
        <DashboardCard title="Coverage" value={`${actionCoverage} actions`}>
          <p>{eventCoverage} EventLog events</p>
        </DashboardCard>
      </div>

      {reports.length > 0 && (
        <label>
          Run history
          <select value={selectedReport?.run_id ?? ""} onChange={(event) => onSelect(event.target.value)}>
            {reports.map((report) => (
              <option key={report.run_id} value={report.run_id}>
                {shortRunId(report.run_id)} / {report.agent_type} / {report.turns_run} turns
              </option>
            ))}
          </select>
        </label>
      )}

      {selectedReport ? (
        <div className="studio-columns">
          <SectionCard title="Safe Replay Summary" description="Replay-like summary without raw StateDelta or hidden content.">
            <dl className="metadata-list">
              <dt>Status</dt>
              <dd>{issueCount ? "failed" : "passed"}</dd>
              <dt>Duration</dt>
              <dd>{playtestDurationSummary(selectedReport, batchReport)}</dd>
              <dt>Failed step</dt>
              <dd>{failedStep ? `#${failedStep.step} ${redactReportText(failedStep.action_type)} / ${redactReportText(failedStep.result)}` : "None"}</dd>
              <dt>Action coverage</dt>
              <dd>{actionCoverage} unique action type(s)</dd>
              <dt>Event coverage</dt>
              <dd>{eventCoverage} EventLog event(s)</dd>
            </dl>
          </SectionCard>
          <SectionCard title="Actions" description="Recent agent inputs through GameLoop.">
            <ItemList
              emptyText="No actions."
              items={selectedReport.actions_taken.slice(-8).map((action) => (
                <span key={`${action.step}-${action.input_text}`}>
                  #{action.step} {redactReportText(action.input_text)} <span className="badge">{redactReportText(action.result)}</span>
                </span>
              ))}
            />
          </SectionCard>
          <SectionCard title="Invariant Violations" description="Rules that failed during the run.">
            <ItemList
              emptyText="No invariant violations."
              items={selectedReport.invariant_violations.map((item) => <span key={item}>{redactReportText(item)}</span>)}
            />
          </SectionCard>
          <SectionCard title="Visibility / Save Checks" description="Leak checks and save/load round trips.">
            <ItemList
              emptyText="No visibility leaks or save/load failures."
              items={[...selectedReport.visibility_leaks, ...selectedReport.save_load_failures].map((item) => (
                <span key={item}>{redactReportText(item)}</span>
              ))}
            />
          </SectionCard>
          <SectionCard title="Hidden Leak Warnings" description="Safe leak warnings only; hidden text is never printed.">
            <ItemList
              emptyText="No hidden leak warnings."
              items={selectedReport.visibility_leaks.map((item) => <span key={item}>{redactLeakSummary(item)}</span>)}
            />
          </SectionCard>
        </div>
      ) : (
        <EmptyState title="No playtest selected." detail="Run a deterministic playtest suite to inspect pass/fail, failed steps, coverage, and safe replay summaries." />
      )}

      {selectedReport && (
        <section className="studio-section">
          <h3>Final State Summary</h3>
          <dl className="metadata-list">
            <dt>World</dt>
            <dd>{selectedReport.final_state_summary.world_id}</dd>
            <dt>Turn</dt>
            <dd>{selectedReport.final_state_summary.turn}</dd>
            <dt>Location</dt>
            <dd>{selectedReport.final_state_summary.location_id}</dd>
            <dt>Events</dt>
            <dd>{selectedReport.final_state_summary.event_count}</dd>
          </dl>
        </section>
      )}
    </section>
  );
}

function firstFailedPlaytestStep(report: PlaytestReport): PlaytestActionRecord | null {
  return report.actions_taken.find((action) => !/success|ok|observed|moved|waited/i.test(action.result)) ?? null;
}

function playtestDurationSummary(report: PlaytestReport, batchReport: PlaytestBatchRun | null): string {
  const batchItem = batchReport?.run_items.find((item) => item.report.run_id === report.run_id);
  if (batchItem) {
    return `${Math.round(batchItem.duration_ms)}ms`;
  }
  return "single run duration not reported";
}

function ScenarioRegressionDashboard({
  cases,
  runs,
  selectedRun,
  error,
  onRun,
  onSelect,
  onRefresh
}: {
  cases: ScenarioRegressionCase[];
  runs: ScenarioRegressionRun[];
  selectedRun: ScenarioRegressionRun | null;
  error: string;
  onRun: (options: { worldId: string; scenarioIds: string[] }) => void;
  onSelect: (runId: string) => void;
  onRefresh: () => void;
}) {
  const [worldId, setWorldId] = useState<string>("mist_valley");
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("all");
  const filteredCases = cases.filter((item) => item.world_id === worldId);
  const selectedCaseIds =
    selectedScenarioId === "all"
      ? filteredCases.map((item) => item.id)
      : selectedScenarioId
        ? [selectedScenarioId]
        : [];
  const failedCases = selectedRun?.case_results.filter((result) => !result.passed) ?? [];

  return (
    <section className="studio-section scenario-regression-dashboard">
      <div className="mod-detail-header">
        <div>
          <h3>Scenario Regression</h3>
          <p className="muted">
            Deterministic story-path checks for visible facts, quests, inventory, hidden boundaries, and save stability.
          </p>
        </div>
        <button type="button" onClick={onRefresh}>
          Refresh Scenarios
        </button>
      </div>
      <ErrorPanel message={error} compact />
      {error.toLowerCase().includes("disabled") && (
        <div className="notice api-disabled-notice">
          Scenario regression API is disabled. Enable local playtest or eval API.
        </div>
      )}

      <div className="playtest-controls">
        <label>
          World
          <select value={worldId} onChange={(event) => setWorldId(event.target.value)}>
            {WORLD_OPTIONS.map((world) => (
              <option key={world.id} value={world.id}>{world.name}</option>
            ))}
          </select>
        </label>
        <label>
          Scenario
          <select value={selectedScenarioId} onChange={(event) => setSelectedScenarioId(event.target.value)}>
            <option value="all">All scenarios</option>
            {filteredCases.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => onRun({ worldId, scenarioIds: selectedCaseIds })}
          disabled={selectedCaseIds.length === 0}
        >
          Run Suite
        </button>
      </div>

      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Cases" value={String(filteredCases.length)}>
          <p>{selectedCaseIds.length} selected</p>
        </DashboardCard>
        <DashboardCard title="Runs" value={String(runs.length)}>
          <p>local in-memory reports</p>
        </DashboardCard>
        <DashboardCard title="Pass" value={String(selectedRun?.passed ?? 0)}>
          <p>{selectedRun ? `${selectedRun.total_cases} total` : "No run selected"}</p>
        </DashboardCard>
        <DashboardCard title="Fail" value={String(selectedRun?.failed ?? 0)}>
          <p>safe summaries only</p>
        </DashboardCard>
      </div>

      {runs.length > 0 && (
        <label>
          Run history
          <select value={selectedRun?.run_id ?? ""} onChange={(event) => onSelect(event.target.value)}>
            {runs.map((run) => (
              <option key={run.run_id} value={run.run_id}>
                {shortRunId(run.run_id)} / {run.passed}-{run.failed} / {run.world_id ?? "mixed"}
              </option>
            ))}
          </select>
        </label>
      )}

      <div className="studio-columns">
        <SectionCard title="Scenario Cases" description="Configured local regression checks.">
          <ItemList
            emptyText="No scenario cases available."
            items={filteredCases.map((item) => (
              <span key={item.id}>
                <strong>{item.name}</strong> <span className="badge">{item.tags.join(", ") || "untagged"}</span>
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="Failed Cases" description="Expected vs actual safe summaries.">
          <ItemList
            emptyText="No failed cases."
            items={failedCases.map((result) => (
              <span key={result.case_id}>
                <strong>{result.name}</strong>
                {result.failed_step !== null && result.failed_step !== undefined && ` step ${result.failed_step}`}
                {result.failure_reasons.length > 0 && `: ${result.failure_reasons.map(redactReportText).join("; ")}`}
              </span>
            ))}
          />
        </SectionCard>
        <SectionCard title="Hidden / Save Checks" description="Leak summary and save/load failures.">
          <ItemList
            emptyText="No hidden leak or save/load failures."
            items={(selectedRun?.case_results ?? []).flatMap((result) => [
              ...result.hidden_leak_summary.map((item) => (
                <span key={`${result.case_id}-leak-${item}`}>{result.name}: {redactReportText(item)}</span>
              )),
              ...(result.save_load_failure
                ? [<span key={`${result.case_id}-save`}>{result.name}: {result.save_load_failure}</span>]
                : [])
            ])}
          />
        </SectionCard>
      </div>

      {selectedRun && (
        <section>
          <h3>Case Results</h3>
          <div className="debug-event-list">
            {selectedRun.case_results.map((result) => (
              <details className="timeline-event" key={result.case_id}>
                <summary>
                  <span>{result.passed ? "pass" : "fail"}</span>
                  <span>{result.name}</span>
                  <span>{result.world_id}</span>
                  <span>{result.failure_reasons.length} issues</span>
                </summary>
                <div className="scenario-result-grid">
                  <div>
                    <strong>Expected</strong>
                    <AuthoringPreviewCode content={JSON.stringify(result.expected_summary, null, 2)} />
                  </div>
                  <div>
                    <strong>Actual</strong>
                    <AuthoringPreviewCode content={JSON.stringify(result.actual_summary, null, 2)} />
                  </div>
                </div>
              </details>
            ))}
          </div>
        </section>
      )}
    </section>
  );
}

function PromptLabPage({
  summary,
  configError,
  projectId,
  onSelectPromptProfile
}: {
  summary: StudioConfigSummary | null;
  configError: string;
  projectId: string;
  onSelectPromptProfile: (profileId: string) => void;
}) {
  const [capabilities, setCapabilities] = useState<ProviderCapabilityCatalog | null>(null);
  const [benchmarkReport, setBenchmarkReport] = useState<ProviderBenchmarkReport | null>(null);
  const [structuredReport, setStructuredReport] = useState<StructuredOutputReliabilityReport | null>(null);
  const [regressionReport, setRegressionReport] = useState<PromptRegressionReport | null>(null);
  const [diagnosticReport, setDiagnosticReport] = useState<LocalModelDiagnosticReport | null>(null);
  const [usageSummary, setUsageSummary] = useState<ModelUsageSummary | null>(null);
  const [recentUsage, setRecentUsage] = useState<ModelUsageRecord[]>([]);
  const [projectUsageSummary, setProjectUsageSummary] = useState<ModelUsageSummary | null>(null);
  const [projectRecentUsage, setProjectRecentUsage] = useState<ModelUsageRecord[]>([]);
  const [usageByMode, setUsageByMode] = useState<CostLatencyGroupSummary[]>([]);
  const [usageByProvider, setUsageByProvider] = useState<CostLatencyGroupSummary[]>([]);
  const [usageRange, setUsageRange] = useState<number | undefined>(undefined);
  const [providerProfiles, setProviderProfiles] = useState<ProviderProfileSummary[]>([]);
  const [providerCapabilityMatrix, setProviderCapabilityMatrix] = useState<ProviderModelCapabilityMatrix | null>(null);
  const [providerStatus, setProviderStatus] = useState<Record<string, unknown> | null>(null);
  const [providerStatusById, setProviderStatusById] = useState<Record<string, Record<string, unknown>>>({});
  const [providerLastTestedById, setProviderLastTestedById] = useState<Record<string, string>>({});
  const [modelAssignmentOpen, setModelAssignmentOpen] = useState(false);
  const [providerValidation, setProviderValidation] = useState<string>("");
  const [providerDraft, setProviderDraft] = useState<ProviderProfileDraft>({
    provider_profile_id: "local_stub",
    display_name: "Local Stub",
    provider_type: "local_stub",
    api_key_env: "",
    secret_ref: "",
    model_profiles: [{ model_id: "local_stub", display_name: "Local Stub", supports_json: true, supports_streaming: false }],
    allowed_modes: ["novel", "tavern", "world", "cross_mode", "quality"],
    default_timeout_seconds: 30,
    enabled: true,
    requires_api_key: false
  });
  const [diffReport, setDiffReport] = useState<PromptDiffReport | null>(null);
  const [labError, setLabError] = useState<string>("");

  async function runLabAction(action: () => Promise<void>) {
    setLabError("");
    try {
      await action();
    } catch (err) {
      setLabError(toErrorMessage(err));
    }
  }

  const profiles = summary?.prompt_profiles ?? [];
  const leftProfile = profiles[0] ? { id: profiles[0].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : {};
  const rightProfile = profiles[1] ? { id: profiles[1].id, hidden_fact_policy: "deny", state_modification_policy: "deny" } : leftProfile;

  async function loadProjectUsage() {
    const [summaryResult, recentResult, byModeResult, byProviderResult] = await Promise.all([
      fetchProjectProviderUsageSummary(projectId, usageRange),
      fetchProjectProviderUsageRecent(projectId, 12, usageRange),
      fetchProjectProviderUsageByMode(projectId, usageRange),
      fetchProjectProviderUsageByProvider(projectId, usageRange)
    ]);
    setProjectUsageSummary(summaryResult);
    setProjectRecentUsage(recentResult.records);
    setUsageByMode(byModeResult.by_mode);
    setUsageByProvider(byProviderResult.by_provider);
  }

  async function loadProviderProfiles() {
    const [profilesResult, matrixResult] = await Promise.all([
      fetchProjectProviders(projectId),
      fetchProjectProviderCapabilityMatrix(projectId)
    ]);
    setProviderProfiles(profilesResult.providers);
    setProviderCapabilityMatrix(matrixResult.matrix);
  }

  async function saveProviderProfile(event: FormEvent) {
    event.preventDefault();
    const cleaned: ProviderProfileDraft = {
      ...providerDraft,
      base_url: providerDraft.base_url?.trim() || null,
      base_url_env: providerDraft.base_url_env?.trim() || null,
      api_key_env: providerDraft.api_key_env?.trim() || null,
      secret_ref: providerDraft.secret_ref?.trim() || null,
      allowed_modes: providerDraft.allowed_modes ?? [],
      model_profiles: providerDraft.model_profiles.filter((model) => model.model_id.trim()).map((model) => ({
        ...model,
        model_id: model.model_id.trim(),
        display_name: model.display_name?.trim() || model.model_id.trim(),
        recommended_use_cases: model.recommended_use_cases ?? []
      }))
    };
    const created = await createProjectProvider(projectId, cleaned);
    setProviderProfiles((current) => [...current.filter((item) => item.provider_profile_id !== created.provider.provider_profile_id), created.provider]);
    setProviderValidation("Profile saved. Secrets are still resolved only on the backend from env or local secret refs.");
  }

  async function validateProvider(profileId: string) {
    const result = await validateProjectProvider(projectId, profileId);
    setProviderValidation(result.ok ? "Provider profile validates." : `Provider profile failed validation: ${result.warnings.join(", ")}`);
    setProviderLastTestedById((current) => ({ ...current, [profileId]: new Date().toISOString() }));
  }

  async function loadProviderStatus(profileId: string) {
    const result = await fetchProjectProviderStatus(projectId, profileId);
    setProviderStatus(result.status);
    setProviderStatusById((current) => ({ ...current, [profileId]: result.status }));
    setProviderLastTestedById((current) => ({ ...current, [profileId]: new Date().toISOString() }));
  }

  return (
    <section className="studio-section">
      <div className="authoring-pane-header">
        <div>
          <h3>Prompt Lab</h3>
          <p className="muted">Unified local model and prompt workbench. All summaries are redacted and local-only.</p>
        </div>
        <StatusBadge label={summary?.debug_api_enabled || summary?.performance_logging_enabled ? "Local APIs ready" : "API gated"} enabled={Boolean(summary?.debug_api_enabled || summary?.performance_logging_enabled)} />
      </div>
      <ErrorPanel message={labError || configError} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Provider" value={summary?.llm_provider ?? "unknown"}>
          <p>{summary?.provider_sends_prompts_off_machine ? "External provider requires explicit opt-in for real tests." : "No real provider call is made by default."}</p>
        </DashboardCard>
        <DashboardCard title="API Key" value={summary?.api_key_configured ? "configured" : "not shown"}>
          <p>Key values never render in Prompt Lab.</p>
        </DashboardCard>
        <DashboardCard title="Hidden Data" value="redacted">
          <p>Normal UI does not show hidden facts, raw env, or raw prompts.</p>
        </DashboardCard>
      </div>

      <ProviderConnectivityDashboard
        profiles={providerProfiles}
        matrix={providerCapabilityMatrix}
        statusById={providerStatusById}
        lastTestedById={providerLastTestedById}
        modelAssignmentOpen={modelAssignmentOpen}
        onTestConnection={(profileId) => void runLabAction(async () => {
          await validateProvider(profileId);
          await loadProviderStatus(profileId);
        })}
        onFetchModels={() => void runLabAction(loadProviderProfiles)}
        onRefreshModels={() => void runLabAction(loadProviderProfiles)}
        onOpenModelAssignment={() => setModelAssignmentOpen((open) => !open)}
        onOpenProviderSetup={() => {
          document.querySelector(".provider-profile-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
        }}
      />

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Provider Capabilities</h4>
            <p className="muted">Declared provider/model metadata only; no network probe.</p>
          </div>
          <button type="button" onClick={() => void runLabAction(async () => setCapabilities(await fetchProviderCapabilities()))}>
            Load Capabilities
          </button>
        </div>
        {capabilities ? (
          <ItemList
            emptyText="No providers."
            items={capabilities.providers.map((provider) => (
              <span key={provider.provider_id}>
                {provider.provider_id}: json {provider.supports_json ? "yes" : "no"}, local {provider.local_only ? "yes" : "no"}
              </span>
            ))}
          />
        ) : (
          <p className="muted">Empty until loaded. API disabled states are shown as a safe error instead of exposing config.</p>
        )}
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Provider Profiles</h4>
            <p className="muted">Provider Setup for project-local provider profiles. API keys are never entered here; use env vars or local secret refs only.</p>
          </div>
          <button type="button" onClick={() => void runLabAction(loadProviderProfiles)}>
            Load Profiles
          </button>
        </div>
        <div className="mode-landing-grid">
          <FeatureCard title="openai" detail="Use api_key_env or secret_ref; the frontend never asks for plaintext keys." />
          <FeatureCard title="openai_compatible" detail="Use a local or trusted compatible endpoint with explicit base URL metadata." />
          <FeatureCard title="local_http" detail="Local model endpoint; capability warnings still apply." />
          <FeatureCard title="relay" detail="Relay-style profile metadata only. No API resale or specific relay support is implied." />
          <FeatureCard title="mock / local_stub" detail="Safe defaults for tests and local dry-runs." />
        </div>
        <form className="form-grid provider-profile-form" onSubmit={(event) => void runLabAction(async () => saveProviderProfile(event))}>
          <label>
            Profile ID
            <input
              value={providerDraft.provider_profile_id}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, provider_profile_id: event.target.value }))}
            />
          </label>
          <label>
            Display Name
            <input
              value={providerDraft.display_name}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, display_name: event.target.value }))}
            />
          </label>
          <label>
            Provider Type
            <select
              value={providerDraft.provider_type}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, provider_type: event.target.value }))}
            >
              <option value="local_stub">local_stub</option>
              <option value="mock">mock</option>
              <option value="local_http">local_http</option>
              <option value="openai">openai</option>
              <option value="openai_compatible">openai_compatible</option>
              <option value="relay">relay</option>
            </select>
          </label>
          <label>
            Base URL
            <input
              value={providerDraft.base_url ?? ""}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, base_url: event.target.value }))}
              placeholder="Optional endpoint URL"
            />
          </label>
          <label>
            Base URL Env
            <input
              value={providerDraft.base_url_env ?? ""}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, base_url_env: event.target.value }))}
              placeholder="LOCAL_LLM_BASE_URL"
            />
          </label>
          <label>
            API Key Env
            <input
              value={providerDraft.api_key_env ?? ""}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, api_key_env: event.target.value }))}
              placeholder="OPENAI_API_KEY"
            />
          </label>
          <label>
            Secret Ref
            <input
              value={providerDraft.secret_ref ?? ""}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, secret_ref: event.target.value }))}
              placeholder="local-secret-id"
            />
          </label>
          <label>
            Model ID
            <input
              value={providerDraft.model_profiles[0]?.model_id ?? ""}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, model_profiles: [{ ...(draft.model_profiles[0] ?? {}), model_id: event.target.value }] }))}
            />
          </label>
          <label>
            Timeout Seconds
            <input
              type="number"
              min={1}
              max={600}
              value={providerDraft.default_timeout_seconds ?? 30}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, default_timeout_seconds: Number(event.target.value) || 30 }))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={providerDraft.enabled ?? true}
              onChange={(event) => setProviderDraft((draft) => ({ ...draft, enabled: event.target.checked }))}
            />
            Enabled
          </label>
          <button type="submit">Save Safe Profile</button>
        </form>
        <p className="muted">{providerValidation || "This form intentionally has no plaintext API key field."}</p>
        <div className="studio-grid two-column-grid">
          <ItemList
            emptyText="No provider profiles loaded."
            items={providerProfiles.map((profile) => (
              <span key={profile.provider_profile_id}>
                {profile.display_name} ({profile.provider_type}) - {profile.enabled ? "enabled" : "disabled"} - {profile.model_profiles.length} models
                <button type="button" onClick={() => void runLabAction(async () => validateProvider(profile.provider_profile_id))}>
                  Validate
                </button>
                <button type="button" onClick={() => void runLabAction(async () => loadProviderStatus(profile.provider_profile_id))}>
                  Status
                </button>
              </span>
            ))}
          />
          <ItemList
            emptyText="No capability matrix loaded."
            items={(providerCapabilityMatrix?.rows ?? []).map((row) => (
              <span key={`${row.provider_profile_id}-${row.model_id}`}>
                {row.provider_profile_id}/{row.model_id}: {row.recommended_use_cases.join(", ") || "no use cases"}
                {row.warnings.length ? ` - warnings ${row.warnings.length}` : ""}
              </span>
            ))}
          />
        </div>
        {providerStatus ? <SafeJSON value={providerStatus} /> : null}
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Benchmarks / Reliability / Regression</h4>
            <p className="muted">Runs use fake/mock defaults. Real provider runs require explicit backend opt-in and are not triggered here.</p>
          </div>
          <div className="button-row">
            <button type="button" onClick={() => void runLabAction(async () => setBenchmarkReport(await runProviderBenchmark(false)))}>
              Run Benchmark
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setStructuredReport(await runStructuredOutputReliability(false)))}>
              Run JSON
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setRegressionReport(await runPromptRegressionSuite()))}>
              Run Regression
            </button>
          </div>
        </div>
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Benchmark" value={benchmarkReport?.run_id ? String(benchmarkReport.ok_cases) : "empty"}>
            <p>{benchmarkReport ? `${benchmarkReport.total_cases} cases, leak risks ${benchmarkReport.hidden_leak_risk_count}` : "No benchmark report loaded."}</p>
          </DashboardCard>
          <DashboardCard title="Structured JSON" value={structuredReport ? `${Math.round(structuredReport.schema_valid_rate * 100)}%` : "empty"}>
            <p>{structuredReport ? `${structuredReport.total_cases} cases, hidden policy ${structuredReport.hidden_policy_violation_rate}` : "No structured output report."}</p>
          </DashboardCard>
          <DashboardCard title="Regression" value={regressionReport?.pass_fail ?? "empty"}>
            <p>{regressionReport ? `${regressionReport.safety_blockers.length} safety blockers` : "No prompt regression report."}</p>
          </DashboardCard>
        </div>
      </section>

      <section className="studio-section">
        <div className="authoring-pane-header">
          <div>
            <h4>Prompt Diff / Local Diagnostics / Usage</h4>
            <p className="muted">Diff and diagnostics use redacted inputs. Usage records never include prompts or API keys.</p>
          </div>
          <div className="button-row">
            <button type="button" onClick={() => void runLabAction(async () => setDiffReport(await reviewPromptDiff(leftProfile, rightProfile)))}>
              Review Diff
            </button>
            <button type="button" onClick={() => void runLabAction(async () => setDiagnosticReport(await runLocalModelDiagnostics()))}>
              Diagnose Local
            </button>
            <button
              type="button"
              onClick={() =>
                void runLabAction(async () => {
                  setUsageSummary(await fetchModelUsageSummary());
                  setRecentUsage((await fetchRecentModelUsage(10)).records);
                })
              }
            >
              Load Usage
            </button>
          </div>
        </div>
        <div className="studio-grid compact-dashboard-grid">
          <DashboardCard title="Prompt Diff" value={diffReport ? String(diffReport.changed_sections.length) : "empty"}>
            <p>{diffReport ? `${diffReport.blockers.length} blockers, token delta ${diffReport.token_delta}` : "No diff report."}</p>
          </DashboardCard>
          <DashboardCard title="Local Diagnostics" value={diagnosticReport?.pass_fail ?? "empty"}>
            <p>{diagnosticReport ? `${diagnosticReport.provider_id}, base URL ${diagnosticReport.base_url_configured ? "configured" : "not needed"}` : "No diagnostic run."}</p>
          </DashboardCard>
          <DashboardCard title="Usage Calls" value={usageSummary ? String(usageSummary.total_calls) : "empty"}>
            <p>{usageSummary ? `p50 ${usageSummary.latency_p50_ms}ms / p95 ${usageSummary.latency_p95_ms}ms / cost ${usageSummary.total_cost_estimated}` : "Usage tracking may be disabled."}</p>
          </DashboardCard>
          <DashboardCard title="Error Rate" value={usageSummary ? `${Math.round(usageSummary.error_rate * 100)}%` : "empty"}>
            <p>{usageSummary ? `${usageSummary.failures} failures` : "No usage summary."}</p>
          </DashboardCard>
        </div>
        <ItemList
          emptyText="No recent usage records."
          items={recentUsage.map((record) => (
            <span key={record.usage_id}>
              {record.provider_id}/{record.model_id} {record.use_case}: {record.success ? "ok" : record.error_type ?? "failed"}
            </span>
          ))}
        />
      </section>

      <section className="studio-section">
        <ProviderUsageCostDashboard
          projectId={projectId}
          summary={projectUsageSummary}
          recent={projectRecentUsage}
          usageByMode={usageByMode}
          usageByProvider={usageByProvider}
          usageRange={usageRange}
          onRangeChange={setUsageRange}
          onLoad={() => void runLabAction(loadProjectUsage)}
        />
      </section>

      <PromptLabPanelIndex />

      <SettingsPrivacyPanel summary={summary} error="" onSelectPromptProfile={onSelectPromptProfile} promptLabOnly />
    </section>
  );
}

function ProviderUsageCostDashboard({
  projectId,
  summary,
  recent,
  usageByMode,
  usageByProvider,
  usageRange,
  onRangeChange,
  onLoad
}: {
  projectId: string;
  summary: ModelUsageSummary | null;
  recent: ModelUsageRecord[];
  usageByMode: CostLatencyGroupSummary[];
  usageByProvider: CostLatencyGroupSummary[];
  usageRange: number | undefined;
  onRangeChange: (range: number | undefined) => void;
  onLoad: () => void;
}) {
  const successErrorRows = summary
    ? [
        { key: "success", count: summary.successes, failures: 0, total_tokens_estimated: summary.total_input_tokens_estimated + summary.total_output_tokens_estimated, total_cost_estimated: summary.total_cost_estimated, latency_p50_ms: summary.latency_p50_ms, latency_p95_ms: summary.latency_p95_ms },
        { key: "error", count: summary.failures, failures: summary.failures, total_tokens_estimated: 0, total_cost_estimated: 0, latency_p50_ms: 0, latency_p95_ms: 0 }
      ]
    : [];
  const totalTokens = summary ? summary.total_input_tokens_estimated + summary.total_output_tokens_estimated : 0;

  return (
    <>
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Usage / Cost Dashboard Pro</h4>
          <p className="muted">
            Local estimates for project {projectId}. Prompts, outputs, API keys, hidden facts, mature/private text, and raw state deltas are never displayed.
          </p>
        </div>
        <div className="button-row">
          <select value={usageRange ?? 0} onChange={(event) => onRangeChange(Number(event.target.value) || undefined)} aria-label="Usage time range">
            <option value={0}>All time</option>
            <option value={60}>Last hour</option>
            <option value={1440}>Last day</option>
            <option value={10080}>Last 7 days</option>
          </select>
          <button type="button" onClick={onLoad}>
            Load Project Usage
          </button>
        </div>
      </div>
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Usage Overview" value={summary ? String(summary.total_calls) : "empty"}>
          <p>{summary ? `${summary.successes} ok / ${summary.failures} errors` : "Usage API may be disabled or no local calls have been recorded."}</p>
        </DashboardCard>
        <DashboardCard title="Estimated Tokens" value={summary ? String(totalTokens) : "empty"}>
          <p>{summary ? `input ${summary.total_input_tokens_estimated} / output ${summary.total_output_tokens_estimated}` : "Token estimates only; prompt and output text are not stored here."}</p>
        </DashboardCard>
        <DashboardCard title="Estimated Cost" value={summary ? formatEstimatedCost(summary.total_cost_estimated) : "empty"}>
          <p>Cost is approximate local metadata, not billing-grade and never uploaded.</p>
        </DashboardCard>
        <DashboardCard title="Average Latency" value={summary ? formatDuration(summary.average_latency_ms) : "empty"}>
          <p>{summary ? `p50 ${formatDuration(summary.latency_p50_ms)} / p95 ${formatDuration(summary.latency_p95_ms)}` : "No latency summary."}</p>
        </DashboardCard>
        <DashboardCard title="Error Count" value={summary ? String(summary.failures) : "empty"}>
          <p>{summary ? `${Math.round(summary.error_rate * 100)}% error rate` : "No usage summary."}</p>
        </DashboardCard>
      </div>
      <div className="studio-grid two-column-grid">
        <UsageGroupList title="By provider" emptyText="No usage by provider." rows={usageByProvider} />
        <UsageGroupList title="By model" emptyText="No usage by model." rows={summary?.by_model ?? []} />
        <UsageGroupList title="By mode" emptyText="No usage by mode." rows={usageByMode} />
        <UsageUseCaseList rows={summary?.by_use_case ?? []} />
        <UsageGroupList title="By success/error" emptyText="No success/error usage summary." rows={successErrorRows} />
      </div>
      <ItemList
        emptyText="No project usage records."
        items={recent.map((record) => (
          <span key={record.usage_id}>
            {(record.mode ?? "mode")}/{record.use_case}: {record.provider_id}/{record.model_id} {record.success ? "ok" : record.error_type ?? "failed"} ({record.input_tokens_estimated} in / {record.output_tokens_estimated} out, {formatDuration(record.duration_ms)})
          </span>
        ))}
      />
      <p className="muted">
        Usage records contain metadata only: provider, model, mode, use case, token estimates, estimated cost, latency, and error type. Full prompt/output text and secrets are excluded.
      </p>
    </>
  );
}

function UsageGroupList({ title, emptyText, rows }: { title: string; emptyText: string; rows: CostLatencyGroupSummary[] }) {
  return (
    <SectionCard title={title} description="Safe usage summary only.">
      <ItemList
        emptyText={emptyText}
        items={rows.map((item) => (
          <span key={item.key}>
            {item.key}: {item.count} calls, {item.failures} errors, {item.total_tokens_estimated} tokens, cost {formatEstimatedCost(item.total_cost_estimated)}, p50 {formatDuration(item.latency_p50_ms)}
          </span>
        ))}
      />
    </SectionCard>
  );
}

function UsageUseCaseList({ rows }: { rows: ModelUsageSummary["by_use_case"] }) {
  return (
    <SectionCard title="By use case" description="Mode routing and task-level usage distribution.">
      <ItemList
        emptyText="No usage by use case."
        items={rows.map((item) => (
          <span key={item.use_case}>
            {item.use_case}: {item.count} calls, {item.failures} errors, input {item.total_input_tokens_estimated}, output {item.total_output_tokens_estimated}, cost {formatEstimatedCost(item.total_cost_estimated)}, avg {formatDuration(item.average_latency_ms)}
          </span>
        ))}
      />
    </SectionCard>
  );
}

function formatEstimatedCost(value: number): string {
  return `$${value.toFixed(value > 0 && value < 0.01 ? 6 : 4)}`;
}

function PromptLabPanelIndex() {
  const panels = [
    "Provider Capabilities",
    "Provider Benchmark",
    "Prompt A/B Test",
    "Narrator Style Lab",
    "NPC Voice Style Lab",
    "Structured Output Reliability",
    "Context Inspector",
    "Prompt Diff",
    "Model Compatibility Matrix",
    "Routing Rule Editor",
    "Prompt Regression",
    "Local Model Diagnostics",
    "Token Budget Profiles",
    "Model Usage Dashboard"
  ];
  return (
    <section className="studio-section">
      <h4>Prompt Lab Panels</h4>
      <div className="template-grid">
        {panels.map((panel) => (
          <span className="badge" key={panel}>{panel}</span>
        ))}
      </div>
      <p className="muted">Real provider calls are not launched automatically from this page. Hidden/debug fields remain redacted in normal UI.</p>
    </section>
  );
}

function SettingsPrivacyPanel({
  selectedProjectId,
  summary,
  localConfigSummary,
  localConfigIssues,
  localEnvTemplate,
  currentWorkspace,
  recentProjectCount = 0,
  error,
  onSelectPromptProfile,
  onRefreshLocalConfig = () => undefined,
  onGenerateLocalEnvTemplate = () => undefined,
  onClearRecentProjects = () => undefined,
  promptLabOnly = false
}: {
  selectedProjectId?: string;
  summary: StudioConfigSummary | null;
  localConfigSummary?: LocalConfigSummary | null;
  localConfigIssues?: LocalConfigIssue[];
  localEnvTemplate?: LocalEnvTemplateResponse | null;
  currentWorkspace?: ProjectWorkspace | null;
  recentProjectCount?: number;
  error: string;
  onSelectPromptProfile: (profileId: string) => void;
  onRefreshLocalConfig?: () => void;
  onGenerateLocalEnvTemplate?: () => void;
  onClearRecentProjects?: () => void;
  promptLabOnly?: boolean;
}) {
  const [profileAId, setProfileAId] = useState<string>("");
  const [profileBId, setProfileBId] = useState<string>("");
  const [useCase, setUseCase] = useState<PromptABUseCase>("narrator");
  const [abReport, setABReport] = useState<PromptABTestReport | null>(null);
  const [abError, setABError] = useState<string>("");
  const [styleReport, setStyleReport] = useState<NarratorStyleReport | null>(null);
  const [styleError, setStyleError] = useState<string>("");
  const [styleGenreTone, setStyleGenreTone] = useState<string>("grounded");
  const [styleSensoryFocus, setStyleSensoryFocus] = useState<string>("balanced");
  const [styleResponseLength, setStyleResponseLength] = useState<string>("medium");
  const [voiceReport, setVoiceReport] = useState<NPCVoiceStyleReport | null>(null);
  const [voiceError, setVoiceError] = useState<string>("");
  const [voiceNPCId, setVoiceNPCId] = useState<string>("harlan");
  const [voiceTone, setVoiceTone] = useState<string>("calm");
  const [voiceCatchphrase, setVoiceCatchphrase] = useState<string>("steady now");
  const [contextSnapshot, setContextSnapshot] = useState<ContextSnapshot | null>(null);
  const [contextError, setContextError] = useState<string>("");
  const [contextType, setContextType] = useState<ContextInspectType>("narrator");
  const [contextNPCId, setContextNPCId] = useState<string>("npc_sample");
  const [contextIncludeRaw, setContextIncludeRaw] = useState<boolean>(false);
  const [compatibilityMatrix, setCompatibilityMatrix] = useState<ModelCompatibilityMatrix | null>(null);
  const [compatibilityError, setCompatibilityError] = useState<string>("");
  const [routingSummary, setRoutingSummary] = useState<ProviderRoutingSummary | null>(null);
  const [modelAssignmentSummary, setModelAssignmentSummary] = useState<ProjectProviderModelAssignmentSummary | null>(null);
  const [routingPreview, setRoutingPreview] = useState<ProviderRoutingPreview | null>(null);
  const [routingError, setRoutingError] = useState<string>("");
  const [routingUseCase, setRoutingUseCase] = useState<ProviderRoutingUseCase>("narrator");
  const [routingPrimaryProvider, setRoutingPrimaryProvider] = useState<string>("local_stub");
  const [routingPrimaryModel, setRoutingPrimaryModel] = useState<string>("local_stub");
  const [routingFallbackProvider, setRoutingFallbackProvider] = useState<string>("mock");
  const [routingFallbackModel, setRoutingFallbackModel] = useState<string>("mock");
  const [routingRequireJson, setRoutingRequireJson] = useState<boolean>(false);
  const [routingRequireLocalOnly, setRoutingRequireLocalOnly] = useState<boolean>(true);
  const [budgetProfiles, setBudgetProfiles] = useState<TokenBudgetProfile[]>([]);
  const [selectedBudgetProfileId, setSelectedBudgetProfileId] = useState<string>("narrator_balanced");
  const [budgetUseCase, setBudgetUseCase] = useState<TokenBudgetUseCase>("narrator");
  const [budgetMaxTokens, setBudgetMaxTokens] = useState<number>(900);
  const [budgetReport, setBudgetReport] = useState<BudgetReport | null>(null);
  const [budgetError, setBudgetError] = useState<string>("");
  const [compactDisplay, setCompactDisplay] = useState<boolean>(false);
  const [showRedactionBadges, setShowRedactionBadges] = useState<boolean>(true);
  const [logTailSize, setLogTailSize] = useState<number>(200);
  const [matureSettings, setMatureSettings] = useState<MatureSettingsResponse | null>(null);
  const [matureSettingsError, setMatureSettingsError] = useState<string>("");
  const [matureSettingsMessage, setMatureSettingsMessage] = useState<string>("");
  const profiles = summary?.prompt_profiles ?? [];
  const effectiveProfileAId = profileAId || summary?.selected_prompt_profile_id || profiles[0]?.id || "";
  const effectiveProfileBId = profileBId || profiles.find((profile) => profile.id !== effectiveProfileAId)?.id || effectiveProfileAId;

  useEffect(() => {
    if (selectedProjectId && !promptLabOnly) {
      void handleLoadMatureSettings();
    }
  }, [selectedProjectId, promptLabOnly]);

  async function handleLoadMatureSettings() {
    if (!selectedProjectId) {
      setMatureSettingsError("Select a project first.");
      return;
    }
    setMatureSettingsError("");
    setMatureSettingsMessage("");
    try {
      setMatureSettings(await fetchMatureSettings(selectedProjectId));
    } catch (err) {
      setMatureSettings(null);
      setMatureSettingsError(toErrorMessage(err));
    }
  }

  async function handleSaveMatureSettings(patch: Record<string, unknown>) {
    if (!selectedProjectId) {
      setMatureSettingsError("Select a project first.");
      return;
    }
    setMatureSettingsError("");
    setMatureSettingsMessage("");
    try {
      const updated = await updateMatureSettings(selectedProjectId, patch);
      setMatureSettings(updated);
      setMatureSettingsMessage("Mature Module settings saved. Mature content remains governed by age, consent, provider, and export policies.");
    } catch (err) {
      setMatureSettingsError(toErrorMessage(err));
    }
  }

  async function handleRunABTest() {
    if (!effectiveProfileAId || !effectiveProfileBId) {
      setABError("Select two prompt profiles first.");
      return;
    }
    setABError("");
    try {
      const report = await runPromptABTest({
        profile_a_id: effectiveProfileAId,
        profile_b_id: effectiveProfileBId,
        provider_id: "fake",
        use_case: useCase
      });
      setABReport(report);
    } catch (err) {
      setABReport(null);
      setABError(toErrorMessage(err));
    }
  }

  async function handleRunNarratorStyle() {
    if (!effectiveProfileAId) {
      setStyleError("Select a prompt profile first.");
      return;
    }
    setStyleError("");
    try {
      const report = await runNarratorStyleExperiment({
        prompt_profile_id: effectiveProfileAId,
        provider_id: "fake",
        genre_tone: styleGenreTone,
        sensory_focus: styleSensoryFocus,
        response_length: styleResponseLength
      });
      setStyleReport(report);
    } catch (err) {
      setStyleReport(null);
      setStyleError(toErrorMessage(err));
    }
  }

  async function handleRunNPCVoiceStyle() {
    if (!voiceNPCId.trim()) {
      setVoiceError("Enter an NPC id first.");
      return;
    }
    setVoiceError("");
    try {
      const report = await runNPCVoiceStyleExperiment({
        npc_id: voiceNPCId.trim(),
        rp_prompt_profile_id: effectiveProfileAId,
        provider_id: "fake",
        voice_profile_variant: {
          tone: voiceTone,
          sentence_length: "mixed",
          vocabulary_style: "plain",
          catchphrases: voiceCatchphrase ? [voiceCatchphrase] : [],
          speech_habits: ["measured"],
          emotional_tells: ["soft pause"]
        },
        example_dialogue_set: [`${voiceNPCId}: ${voiceCatchphrase || "I answer carefully."}`],
        dialogue_test_cases: [
          {
            id: "local_voice_sample",
            player_line: "What do you know?",
            expected_emotional_tone: voiceTone,
            unknown_fact_terms: ["unknown forbidden fact"],
            hidden_terms: ["the mayor forged the charter"]
          }
        ]
      });
      setVoiceReport(report);
    } catch (err) {
      setVoiceReport(null);
      setVoiceError(toErrorMessage(err));
    }
  }

  async function handleInspectContext() {
    setContextError("");
    try {
      const snapshot = await inspectPromptLabContext({
        context_type: contextType,
        npc_id: contextNPCId || null,
        location_id: "start",
        player_input: "look around",
        include_debug_raw: contextIncludeRaw
      });
      setContextSnapshot(snapshot);
    } catch (err) {
      setContextSnapshot(null);
      setContextError(toErrorMessage(err));
    }
  }

  async function handleLoadCompatibilityMatrix(recompute = false) {
    setCompatibilityError("");
    try {
      const matrix = recompute
        ? await recomputeModelCompatibilityMatrix()
        : await fetchModelCompatibilityMatrix();
      setCompatibilityMatrix(matrix);
    } catch (err) {
      setCompatibilityMatrix(null);
      setCompatibilityError(toErrorMessage(err));
    }
  }

  function currentRoutingRule(): ProviderRoutingRule {
    return {
      use_case: routingUseCase,
      primary_provider_id: routingPrimaryProvider.trim(),
      primary_model_id: routingPrimaryModel.trim(),
      fallback_provider_id: routingFallbackProvider.trim() || null,
      fallback_model_id: routingFallbackModel.trim() || null,
      require_json_support: routingRequireJson || routingUseCaseRequiresJson(routingUseCase),
      require_local_only: routingRequireLocalOnly,
      enabled: true
    };
  }

  function currentRoutingConfig(): { rules: ProviderRoutingRule[] } {
    const existingRules = (modelAssignmentSummary?.rules ?? routingSummary?.rules ?? []).filter((rule) => rule.use_case !== routingUseCase);
    return { rules: [...existingRules, currentRoutingRule()] };
  }

  async function handlePreviewRoutingRule() {
    setRoutingError("");
    try {
      const preview = await previewProviderRoutingRule(currentRoutingRule());
      setRoutingPreview(preview);
    } catch (err) {
      setRoutingPreview(null);
      setRoutingError(toErrorMessage(err));
    }
  }

  async function handleSaveRoutingRule() {
    setRoutingError("");
    try {
      if (selectedProjectId) {
        const saved = await saveProjectProviderModelAssignments(selectedProjectId, currentRoutingConfig());
        setModelAssignmentSummary(saved);
      } else {
        const saved = await saveProviderRoutingConfig(currentRoutingConfig());
        setRoutingSummary(saved);
      }
      setRoutingPreview(null);
    } catch (err) {
      setRoutingError(toErrorMessage(err));
    }
  }

  async function handleValidateModelAssignment() {
    if (!selectedProjectId) {
      setRoutingError("Select a project before validating project model assignments.");
      return;
    }
    setRoutingError("");
    try {
      setModelAssignmentSummary(await validateProjectProviderModelAssignments(selectedProjectId, currentRoutingConfig()));
      setRoutingPreview(null);
    } catch (err) {
      setRoutingError(toErrorMessage(err));
    }
  }

  async function handleLoadRoutingSummary() {
    setRoutingError("");
    try {
      if (selectedProjectId) {
        setModelAssignmentSummary(await fetchProjectProviderModelAssignments(selectedProjectId));
      } else {
        const loaded = await fetchProviderRoutingSummary();
        setRoutingSummary(loaded);
      }
    } catch (err) {
      setRoutingSummary(null);
      setModelAssignmentSummary(null);
      setRoutingError(toErrorMessage(err));
    }
  }

  async function handleLoadBudgetProfiles() {
    setBudgetError("");
    try {
      const response = await fetchTokenBudgetProfiles();
      setBudgetProfiles(response.profiles);
      if (response.profiles.length > 0) {
        const selected = response.profiles.find((profile) => profile.id === selectedBudgetProfileId) ?? response.profiles[0];
        setSelectedBudgetProfileId(selected.id);
        setBudgetUseCase(selected.use_case);
        setBudgetMaxTokens(selected.max_total_tokens);
      }
    } catch (err) {
      setBudgetError(toErrorMessage(err));
    }
  }

  async function handleEstimateBudget() {
    setBudgetError("");
    try {
      const baseProfile = budgetProfiles.find((profile) => profile.id === selectedBudgetProfileId) ?? {
        id: "custom_ui_budget",
        use_case: budgetUseCase,
        max_total_tokens: budgetMaxTokens,
        reserved_output_tokens: 240,
        max_memory_tokens: 160,
        max_lore_tokens: 120,
        max_recent_events_tokens: 160,
        max_dialogue_examples_tokens: 120,
        priority_order: ["safety_constraints", "player_input", "action_result", "visible_facts", "dialogue_profile", "npc_known_facts", "recent_events", "memory", "lore", "dialogue_examples"],
        overflow_policy: "trim_low_priority" as const
      };
      const profile = { ...baseProfile, use_case: budgetUseCase, max_total_tokens: budgetMaxTokens };
      const sections = contextSnapshot?.sections ?? [];
      const report = await estimateTokenBudget(profile, sections);
      setBudgetReport(report);
    } catch (err) {
      setBudgetReport(null);
      setBudgetError(toErrorMessage(err));
    }
  }

  return (
    <section className="studio-section privacy-panel">
      <div className="authoring-pane-header">
        <div>
          <h3>{promptLabOnly ? "Prompt Profiles / Experiments" : "Settings / Local Privacy"}</h3>
          <p className="muted">
            {promptLabOnly
              ? "Prompt profiles and experiment controls. Reports stay redacted and are never applied automatically."
              : "Safe configuration summary without API keys, raw env, or full local paths."}
          </p>
        </div>
        <StatusBadge label={summary?.local_only ? "Local only" : "Unavailable"} enabled={Boolean(summary?.local_only)} />
      </div>
      <ErrorPanel message={error} compact />
      {summary ? (
        <>
          {!promptLabOnly && (
            <section className="studio-section">
              <h4>Settings / Preferences Sections</h4>
              <div className="mode-landing-grid">
                {["General", "Local Privacy", "Providers", "Export", "Debug", "Backup / Restore", "Diagnostics", "Mature Module", "UI Preferences", "Quality Gate"].map((section) => (
                  <FeatureCard key={section} title={section} detail="Local desktop preference summary; no account, cloud sync, online marketplace, raw env, or API key values." />
                ))}
              </div>
            </section>
          )}
          {!promptLabOnly && <ProviderSetupWizardPanel />}
          {!promptLabOnly && (
            <section className="studio-section">
              <div className="section-heading-row">
                <div>
                  <h4>Local Config Manager</h4>
                  <p className="muted">Safe backend config summary. Secrets and raw env are never returned.</p>
                </div>
                <div className="button-row">
                  <button type="button" onClick={onRefreshLocalConfig}>
                    Refresh Config
                  </button>
                  <button type="button" onClick={onGenerateLocalEnvTemplate}>
                    Generate Template
                  </button>
                </div>
              </div>
              {localConfigSummary ? (
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Provider" value={localConfigSummary.provider_type}>
                    <p>{localConfigSummary.model_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Database" value={localConfigSummary.database_configured ? "configured" : "missing"}>
                    <p>{localConfigSummary.database_path_hint}</p>
                  </DashboardCard>
                  <DashboardCard title="API Key" value={localConfigSummary.api_key_configured ? "configured" : "not set"}>
                    <p>Value stays backend-only</p>
                  </DashboardCard>
                  <DashboardCard title="Local APIs" value="safe summary">
                    <p>
                      Authoring {localConfigSummary.authoring_api_enabled ? "on" : "off"},
                      Debug {localConfigSummary.debug_api_enabled ? "on" : "off"}
                    </p>
                  </DashboardCard>
                </div>
              ) : (
                <EmptyState title="No local config summary." detail="Refresh to load the safe backend config summary." />
              )}
              <div className="studio-columns">
                <section>
                  <h4>Config Issues</h4>
                  <ItemList
                    emptyText="No config issues reported."
                    items={(localConfigIssues ?? []).map((issue) => (
                      <span key={`${issue.code}-${issue.safe_field}`}>
                        {issue.severity}: {redactReportText(issue.safe_field)} - {redactReportText(issue.message)}
                      </span>
                    ))}
                  />
                </section>
                <section>
                  <h4>Generated Template</h4>
                  {localEnvTemplate ? (
                    <details>
                      <summary>{localEnvTemplate.file_name} preview</summary>
                      <AuthoringPreviewCode content={localEnvTemplate.template} />
                    </details>
                  ) : (
                    <p className="muted">Generate a safe .env.example-like template with blank secrets.</p>
                  )}
                </section>
              </div>
            </section>
          )}
          {!promptLabOnly && (
            <section className="studio-section desktop-settings-section">
              <div className="section-heading-row">
                <div>
                  <h4>Desktop Settings</h4>
                  <p className="muted">Local UI preferences and safe desktop summaries. This panel cannot write .env or provider secrets.</p>
                </div>
                <StatusBadge label="secrets hidden" enabled />
              </div>
              <div className="studio-grid compact-dashboard-grid">
                <DashboardCard title="Workspace" value={currentWorkspace?.name ?? "none"}>
                  <p>{currentWorkspace?.path_redacted ?? "No workspace selected"}</p>
                  <p className="muted">{currentWorkspace ? `${currentWorkspace.world_count} world pack(s)` : "Add or create a workspace first."}</p>
                </DashboardCard>
                <DashboardCard title="Provider" value={localConfigSummary?.provider_type ?? summary.llm_provider}>
                  <p>{localConfigSummary?.model_id ?? "model hidden or unavailable"}</p>
                  <p className="muted">Safe summary only; API key values are backend-only.</p>
                </DashboardCard>
                <DashboardCard title="Logs" value="redacted">
                  <p>logs/.../local studio logs</p>
                  <p className="muted">Tail size {logTailSize} lines; raw prompts and secrets stay redacted.</p>
                </DashboardCard>
                <DashboardCard title="Backup Defaults" value="safe">
                  <p>Includes worlds, saves, templates, modules, metadata.</p>
                  <p className="muted">Excludes .env, API keys, logs, cache, node_modules, dist.</p>
                </DashboardCard>
              </div>
              <div className="template-grid">
                <label>
                  Log tail size
                  <input
                    type="number"
                    min={50}
                    max={2000}
                    step={50}
                    value={logTailSize}
                    onChange={(event) => setLogTailSize(Number(event.target.value))}
                  />
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={compactDisplay}
                    onChange={(event) => setCompactDisplay(event.target.checked)}
                  />
                  Compact local-only display
                </label>
                <label className="checkbox-row">
                  <input
                    type="checkbox"
                    checked={showRedactionBadges}
                    onChange={(event) => setShowRedactionBadges(event.target.checked)}
                  />
                  Show redaction badges
                </label>
              </div>
              <div className="studio-columns">
                <section>
                  <h4>API Status</h4>
                  <StatusDot label="Authoring" enabled={summary.authoring_api_enabled} />
                  <StatusDot label="Debug" enabled={summary.debug_api_enabled} />
                  <StatusDot label="Eval" enabled={summary.eval_api_enabled} />
                  <StatusDot label="Playtest" enabled={summary.playtest_api_enabled} />
                  <StatusDot label="Quality" enabled={summary.eval_api_enabled || summary.playtest_api_enabled || summary.performance_logging_enabled} />
                </section>
                <section>
                  <h4>Local Data Controls</h4>
                  <p className="muted">Recent project references: {recentProjectCount}. Paths shown to the browser are redacted.</p>
                  <button type="button" onClick={onClearRecentProjects} disabled={recentProjectCount === 0}>
                    Clear Recent Projects
                  </button>
                </section>
              </div>
              <div className="privacy-note-grid">
                <p>{showRedactionBadges ? "Redaction active: API keys, raw env, raw prompts, hidden facts, and full sensitive paths are not displayed." : "Redaction is always active even when badges are hidden."}</p>
                <p>{compactDisplay ? "Compact display preference is local UI state only." : "Standard display preference is local UI state only."}</p>
              </div>
              {!promptLabOnly && (
                <section className="studio-section">
                  <div className="authoring-pane-header">
                    <div>
                      <h4>Mature Module Settings</h4>
                      <p className="muted">Default-off local policy controls. Mature memory bodies, secrets, raw env, and provider keys are not displayed here.</p>
                    </div>
                    <button type="button" disabled={!selectedProjectId} onClick={handleLoadMatureSettings}>Refresh</button>
                  </div>
                  <ErrorPanel message={matureSettingsError} compact />
                  <SuccessPanel message={matureSettingsMessage} compact />
                  <div className="studio-grid compact-dashboard-grid">
                    <DashboardCard title="Mature Module" value={matureSettings?.policy.enabled ? "Enabled" : "Disabled"}>
                      <p className="muted">Disabled by default. Local-only provider routing is recommended.</p>
                    </DashboardCard>
                    <DashboardCard title="Max Rating" value={matureSettings?.policy.max_rating ?? "safe"}>
                      <p className="muted">No minors or unknown-age characters; consent is required.</p>
                    </DashboardCard>
                    <DashboardCard title="Fade-to-Black" value={matureSettings?.policy.default_fade_to_black ? "Default" : "Off"}>
                      <p className="muted">Boundary scenes should use safe transition summaries.</p>
                    </DashboardCard>
                    <DashboardCard title="Mature Export" value={matureSettings?.policy.export_mature_content ? "Explicitly on" : "Default off"}>
                      <p className="muted">Normal export excludes mature memory, boundary private notes, debug memory, and secrets.</p>
                    </DashboardCard>
                  </div>
                  <div className="template-grid">
                    <label className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={Boolean(matureSettings?.policy.enabled)}
                        onChange={(event) => handleSaveMatureSettings({ enabled: event.target.checked })}
                        disabled={!selectedProjectId}
                      />
                      Enable Mature Module policy metadata
                    </label>
                    <label className="checkbox-row">
                      <input
                        type="checkbox"
                        checked={Boolean(matureSettings?.policy.export_mature_content)}
                        onChange={(event) => handleSaveMatureSettings({ export_mature_content: event.target.checked })}
                        disabled={!selectedProjectId}
                      />
                      Allow explicit mature export flag
                    </label>
                  </div>
                  <p className="muted">
                    Provider policy must allow the requested rating. The UI never shows mature memory details, API keys, raw environment values, or hidden facts.
                  </p>
                </section>
              )}
            </section>
          )}
          <div className="studio-grid compact-dashboard-grid">
            <DashboardCard title="Provider" value={summary.llm_provider}>
              <p>{summary.provider_status}</p>
              <p className="muted">
                {summary.provider_sends_prompts_off_machine
                  ? "Prompts may leave this app through the configured provider."
                  : "No off-machine LLM calls are expected for this provider."}
              </p>
            </DashboardCard>
            <DashboardCard title="Database" value={summary.database_configured ? "Configured" : "Missing"}>
              <p>{summary.database_path_hint}</p>
              <p className="muted">Full paths are redacted from the browser.</p>
            </DashboardCard>
            <DashboardCard title="API Key" value={summary.api_key_configured ? "Configured" : "Not configured"}>
              <p className="muted">The key value is never returned to the frontend.</p>
            </DashboardCard>
            <DashboardCard title="Prompt Profile" value={summary.selected_prompt_profile_id}>
              <p className="muted">Profiles adjust style and temperature only; they do not change world rules.</p>
            </DashboardCard>
            <DashboardCard title="Local APIs" value="Status">
              <StatusDot label="Authoring" enabled={summary.authoring_api_enabled} />
              <StatusDot label="Debug" enabled={summary.debug_api_enabled} />
              <StatusDot label="Performance" enabled={summary.performance_logging_enabled} />
              <StatusDot label="Playtest" enabled={summary.playtest_api_enabled} />
              <StatusDot label="Eval" enabled={summary.eval_api_enabled} />
            </DashboardCard>
          </div>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Prompt Profiles</h4>
                <p className="muted">Local prompt preferences. Hidden facts and raw state are never added by profiles.</p>
              </div>
            </div>
            <div className="template-grid">
              <label>
                Selected profile
                <select
                  value={summary.selected_prompt_profile_id}
                  onChange={(event) => onSelectPromptProfile(event.target.value)}
                >
                  {summary.prompt_profiles.map((profile) => (
                    <option key={profile.id} value={profile.id} disabled={!profile.enabled}>
                      {profile.name}{profile.matches_current_provider ? "" : " (provider mismatch)"}
                    </option>
                  ))}
                </select>
              </label>
              <div>
                {summary.prompt_profiles
                  .filter((profile) => profile.id === summary.selected_prompt_profile_id)
                  .map((profile) => (
                    <div key={profile.id}>
                      <p className="muted">{profile.description}</p>
                      <span className="badge">{profile.narrator_prompt_variant}</span>
                      <span className="badge">{profile.rp_profile.name}</span>
                      <span className="chip">narrator {profile.temperature_overrides.narrator ?? "default"}</span>
                      <span className="chip">providers {profile.provider_filter.join(", ")}</span>
                      <p className="muted">
                        RP: {profile.rp_profile.dialogue_depth}, {profile.rp_profile.emotional_intensity},{" "}
                        {profile.rp_profile.prose_density}; hidden facts {profile.rp_profile.hidden_fact_policy},
                        state changes {profile.rp_profile.state_modification_policy}.
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Prompt Lab A/B</h4>
                <p className="muted">Compare prompt profiles with fake provider output. Results are redacted and are never applied automatically.</p>
              </div>
              <button type="button" onClick={() => void handleRunABTest()}>
                Run A/B
              </button>
            </div>
            <ErrorPanel message={abError} compact />
            <div className="template-grid">
              <label>
                Profile A
                <select value={effectiveProfileAId} onChange={(event) => setProfileAId(event.target.value)}>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Profile B
                <select value={effectiveProfileBId} onChange={(event) => setProfileBId(event.target.value)}>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Use case
                <select value={useCase} onChange={(event) => setUseCase(event.target.value as PromptABUseCase)}>
                  <option value="narrator">Narrator</option>
                  <option value="RP_dialogue">RP dialogue</option>
                  <option value="intent_parser">Intent parser</option>
                  <option value="memory_summary">Memory summary</option>
                </select>
              </label>
            </div>
            {abReport ? (
              <div className="studio-grid compact-dashboard-grid">
                <DashboardCard title="Result" value={abReport.pass_fail}>
                  <p>{abReport.run_id}</p>
                </DashboardCard>
                <DashboardCard title="Schema" value={Object.values(abReport.schema_reliability).join(" / ") || "n/a"}>
                  <p>Reliability by profile</p>
                </DashboardCard>
                <DashboardCard title="Hidden leaks" value={String(abReport.hidden_leak_flags.length)}>
                  <p>Hidden details are redacted from this report.</p>
                </DashboardCard>
                <DashboardCard title="Latency" value={`${abReport.latency_cost_summary.average_latency_ms ?? 0}ms`}>
                  <p>Estimated cost {abReport.latency_cost_summary.estimated_cost ?? 0}</p>
                </DashboardCard>
              </div>
            ) : (
              <p className="muted">Run a local A/B test to compare style, schema reliability, hidden leak flags, and latency.</p>
            )}
            {abReport && (
              <ItemList
                emptyText="No case results."
                items={abReport.cases.map((caseResult) => (
                  <span key={caseResult.case_id}>
                    {caseResult.case_id}: {caseResult.variant_a.profile_id} {caseResult.variant_a.ok ? "ok" : "fail"} /{" "}
                    {caseResult.variant_b.profile_id} {caseResult.variant_b.ok ? "ok" : "fail"}
                  </span>
                ))}
              />
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Narrator Style Lab</h4>
                <p className="muted">Test narrator style parameters with fake output and deterministic safety checks.</p>
              </div>
              <button type="button" onClick={() => void handleRunNarratorStyle()}>
                Run Style
              </button>
            </div>
            <ErrorPanel message={styleError} compact />
            <div className="template-grid">
              <label>
                Profile
                <select value={effectiveProfileAId} onChange={(event) => setProfileAId(event.target.value)}>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Genre tone
                <input value={styleGenreTone} onChange={(event) => setStyleGenreTone(event.target.value)} />
              </label>
              <label>
                Sensory focus
                <input value={styleSensoryFocus} onChange={(event) => setStyleSensoryFocus(event.target.value)} />
              </label>
              <label>
                Response length
                <select value={styleResponseLength} onChange={(event) => setStyleResponseLength(event.target.value)}>
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </label>
            </div>
            {styleReport ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Result" value={styleReport.pass_fail}>
                    <p>{styleReport.run_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Style score" value={String(styleReport.style_score)}>
                    <p>{styleReport.output_summary_safe || "No output summary"}</p>
                  </DashboardCard>
                  <DashboardCard title="Latency" value={`${styleReport.latency_ms}ms`}>
                    <p>Provider {styleReport.provider_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Blockers" value={String(styleReport.blockers.length)}>
                    <p>Hidden text remains redacted.</p>
                  </DashboardCard>
                </div>
                <ItemList
                  emptyText="No findings."
                  items={styleReport.findings.map((finding) => (
                    <span key={finding.check}>
                      {finding.check}: {finding.passed ? "pass" : finding.severity}
                    </span>
                  ))}
                />
              </>
            ) : (
              <p className="muted">Run a local narrator style experiment to check style match, hidden leaks, invented items, consistency, and action suggestions.</p>
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>NPC Voice Style Lab</h4>
                <p className="muted">Compare NPC voice settings with fake dialogue output. Examples are style-only and do not become facts.</p>
              </div>
              <button type="button" onClick={() => void handleRunNPCVoiceStyle()}>
                Run Voice
              </button>
            </div>
            <ErrorPanel message={voiceError} compact />
            <div className="template-grid">
              <label>
                NPC id
                <input value={voiceNPCId} onChange={(event) => setVoiceNPCId(event.target.value)} />
              </label>
              <label>
                RP profile
                <select value={effectiveProfileAId} onChange={(event) => setProfileAId(event.target.value)}>
                  {profiles.map((profile) => (
                    <option key={profile.id} value={profile.id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Tone
                <input value={voiceTone} onChange={(event) => setVoiceTone(event.target.value)} />
              </label>
              <label>
                Catchphrase
                <input value={voiceCatchphrase} onChange={(event) => setVoiceCatchphrase(event.target.value)} />
              </label>
            </div>
            {voiceReport ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Result" value={voiceReport.pass_fail}>
                    <p>{voiceReport.run_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Voice score" value={String(voiceReport.voice_consistency_score)}>
                    <p>{voiceReport.output_summaries_safe[0] || "No output summary"}</p>
                  </DashboardCard>
                  <DashboardCard title="Latency" value={`${voiceReport.latency_ms}ms`}>
                    <p>Provider {voiceReport.provider_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Blockers" value={String(voiceReport.blockers.length)}>
                    <p>Unknown and hidden facts remain redacted.</p>
                  </DashboardCard>
                </div>
                <ItemList
                  emptyText="No findings."
                  items={voiceReport.findings.map((finding) => (
                    <span key={`${finding.case_id}-${finding.check}`}>
                      {finding.case_id} / {finding.check}: {finding.passed ? "pass" : finding.severity}
                    </span>
                  ))}
                />
              </>
            ) : (
              <p className="muted">Run a local NPC voice experiment to check consistency, catchphrases, tone, unknown facts, hidden leaks, relationship values, and quest claims.</p>
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Context Builder Inspector</h4>
                <p className="muted">Inspect prompt context sections, token estimates, visibility partitions, and exclusion reasons.</p>
              </div>
              <button type="button" onClick={() => void handleInspectContext()}>
                Inspect Context
              </button>
            </div>
            <ErrorPanel message={contextError} compact />
            <div className="template-grid">
              <label>
                Context type
                <select value={contextType} onChange={(event) => setContextType(event.target.value as ContextInspectType)}>
                  <option value="narrator">Narrator</option>
                  <option value="dialogue">Dialogue</option>
                  <option value="group_rp">Group RP</option>
                  <option value="intent_parser">Intent parser</option>
                  <option value="memory_summary">Memory summary</option>
                  <option value="character_import">Character import</option>
                </select>
              </label>
              <label>
                NPC id
                <input value={contextNPCId} onChange={(event) => setContextNPCId(event.target.value)} />
              </label>
              <label>
                Debug raw redacted
                <input
                  type="checkbox"
                  checked={contextIncludeRaw}
                  onChange={(event) => setContextIncludeRaw(event.target.checked)}
                />
              </label>
            </div>
            {contextSnapshot ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Context" value={contextSnapshot.context_type}>
                    <p>{contextSnapshot.snapshot_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Tokens" value={String(contextSnapshot.total_token_estimate)}>
                    <p>{contextSnapshot.sections.length} sections</p>
                  </DashboardCard>
                  <DashboardCard title="Raw prompt" value={contextSnapshot.raw_prompt_included ? "redacted" : "hidden"}>
                    <p>Hidden/debug sections stay redacted by default.</p>
                  </DashboardCard>
                </div>
                <ItemList
                  emptyText="No context sections."
                  items={contextSnapshot.sections.map((section, index) => (
                    <span key={`${section.section_type}-${index}`}>
                      {section.section_type} [{section.visibility_level}] {section.token_estimate} tokens
                      {section.excluded_reasons.length ? ` (${section.excluded_reasons.join(", ")})` : ""}:{" "}
                      {section.safe_summary}
                    </span>
                  ))}
                />
                {contextSnapshot.raw_prompt_redacted && (
                  <details className="timeline-event">
                    <summary>Redacted debug raw prompt</summary>
                    <pre>{contextSnapshot.raw_prompt_redacted}</pre>
                  </details>
                )}
              </>
            ) : (
              <p className="muted">Run the inspector to see context composition without exposing hidden content to normal UI.</p>
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Token Budget Manager</h4>
                <p className="muted">Estimate and trim context sections while preserving safety constraints and hidden redaction.</p>
              </div>
              <div className="button-row">
                <button type="button" onClick={() => void handleLoadBudgetProfiles()}>
                  Load Profiles
                </button>
                <button type="button" onClick={() => void handleEstimateBudget()}>
                  Estimate Budget
                </button>
              </div>
            </div>
            <ErrorPanel message={budgetError} compact />
            <div className="template-grid">
              <label>
                Budget profile
                <select value={selectedBudgetProfileId} onChange={(event) => setSelectedBudgetProfileId(event.target.value)}>
                  {(budgetProfiles.length ? budgetProfiles : [{ id: "custom_ui_budget", use_case: budgetUseCase } as TokenBudgetProfile]).map((profile) => (
                    <option key={profile.id} value={profile.id}>{profile.id}</option>
                  ))}
                </select>
              </label>
              <label>
                Use case
                <select value={budgetUseCase} onChange={(event) => setBudgetUseCase(event.target.value as TokenBudgetUseCase)}>
                  <option value="narrator">Narrator</option>
                  <option value="dialogue">Dialogue</option>
                  <option value="group_rp">Group RP</option>
                  <option value="intent_parser">Intent parser</option>
                  <option value="memory_summary">Memory summary</option>
                  <option value="character_import">Character import</option>
                </select>
              </label>
              <label>
                Max total tokens
                <input type="number" min={64} value={budgetMaxTokens} onChange={(event) => setBudgetMaxTokens(Number(event.target.value))} />
              </label>
            </div>
            {budgetReport ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Input" value={String(budgetReport.input_token_estimate)}>
                    <p>{budgetReport.profile.id}</p>
                  </DashboardCard>
                  <DashboardCard title="Final" value={String(budgetReport.final_context_tokens)}>
                    <p>Available {budgetReport.available_context_tokens}</p>
                  </DashboardCard>
                  <DashboardCard title="Trimmed" value={String(budgetReport.trimmed_sections.length)}>
                    <p>{budgetReport.trimmed_sections.join(", ") || "None"}</p>
                  </DashboardCard>
                  <DashboardCard title="Dropped" value={String(budgetReport.dropped_sections.length)}>
                    <p>{budgetReport.blockers.join(", ") || "No blockers"}</p>
                  </DashboardCard>
                </div>
                <ItemList
                  emptyText="No budget sections."
                  items={budgetReport.sections.slice(0, 12).map((section, index) => (
                    <span key={`${section.section_type}-${index}`}>
                      {section.section_type}: {section.original_tokens} {"->"} {section.final_tokens}
                      {section.protected ? " protected" : section.dropped ? " dropped" : section.trimmed_tokens ? " trimmed" : ""}
                    </span>
                  ))}
                />
              </>
            ) : (
              <p className="muted">Use the latest Context Inspector snapshot or the backend sample context to estimate budget trimming.</p>
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Model Compatibility Matrix</h4>
                <p className="muted">Summarize declared capabilities, local benchmark reports, schema reliability, and safe latency metadata.</p>
              </div>
              <div className="button-row">
                <button type="button" onClick={() => void handleLoadCompatibilityMatrix(false)}>
                  Load Matrix
                </button>
                <button type="button" onClick={() => void handleLoadCompatibilityMatrix(true)}>
                  Recompute
                </button>
              </div>
            </div>
            <ErrorPanel message={compatibilityError} compact />
            {compatibilityMatrix ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Models" value={String(compatibilityMatrix.source_summary.declared_model_count ?? 0)}>
                    <p>{compatibilityMatrix.matrix_id}</p>
                  </DashboardCard>
                  <DashboardCard title="Use cases" value={String(compatibilityMatrix.use_cases.length)}>
                    <p>{compatibilityMatrix.generated_at}</p>
                  </DashboardCard>
                  <DashboardCard title="Warnings" value={String(compatibilityMatrix.warnings.length)}>
                    <p>{compatibilityMatrix.warnings.join(", ") || "None"}</p>
                  </DashboardCard>
                  <DashboardCard title="Blockers" value={String(compatibilityMatrix.blockers.length)}>
                    <p>No API keys or hidden prompts are shown.</p>
                  </DashboardCard>
                </div>
                <div className="debug-event-list">
                  {compatibilityMatrix.rows.slice(0, 24).map((row) => (
                    <div
                      className={`timeline-event ${row.unsupported ? "danger" : row.caution ? "warning" : "safe"}`}
                      key={`${row.provider_id}-${row.model_id}-${row.use_case}`}
                    >
                      <strong>{row.provider_id}/{row.model_id}</strong>
                      <span className="chip">{row.use_case}</span>
                      <ModelCapabilityBadge label={row.unsupported ? "unsupported" : row.caution ? "caution" : row.recommended ? "recommended" : "supported"} supported={!row.unsupported} />
                      <p className="muted">{row.reason}</p>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="muted">Load the matrix to compare provider/model fit without running real providers or exposing hidden cases.</p>
            )}
          </section>
          <section className="studio-section">
            <div className="authoring-pane-header">
              <div>
                <h4>Provider Model Assignment by Mode</h4>
                <p className="muted">Assign provider/model pairs for Novel, Tavern, World, Cross-Mode, Quality, and summary use cases. This validates metadata only and never calls providers.</p>
              </div>
              <div className="button-row">
                <button type="button" onClick={() => void handleLoadRoutingSummary()}>
                  Load Assignments
                </button>
                <button type="button" onClick={() => void handlePreviewRoutingRule()}>
                  Preview Rule
                </button>
                <button type="button" onClick={() => void handleValidateModelAssignment()}>
                  Validate Assignment
                </button>
                <button type="button" onClick={() => void handleSaveRoutingRule()}>
                  Save Assignment
                </button>
              </div>
            </div>
            <ErrorPanel message={routingError} compact />
            <div className="template-grid">
              <label>
                Use case
                <select value={routingUseCase} onChange={(event) => setRoutingUseCase(event.target.value as ProviderRoutingUseCase)}>
                  {PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map((useCase) => (
                    <option key={useCase.value} value={useCase.value}>{useCase.label}</option>
                  ))}
                </select>
              </label>
              <label>
                Primary provider
                <input list="provider-routing-provider-options" value={routingPrimaryProvider} onChange={(event) => setRoutingPrimaryProvider(event.target.value)} />
              </label>
              <label>
                Primary model
                <input list="provider-routing-model-options" value={routingPrimaryModel} onChange={(event) => setRoutingPrimaryModel(event.target.value)} />
              </label>
              <label>
                Fallback provider
                <input list="provider-routing-provider-options" value={routingFallbackProvider} onChange={(event) => setRoutingFallbackProvider(event.target.value)} />
              </label>
              <label>
                Fallback model
                <input list="provider-routing-model-options" value={routingFallbackModel} onChange={(event) => setRoutingFallbackModel(event.target.value)} />
              </label>
              <datalist id="provider-routing-provider-options">
                <option value="local_stub" />
                <option value="mock" />
                <option value="openai" />
                <option value="openai_compatible" />
                <option value="relay" />
                <option value="custom" />
              </datalist>
              <datalist id="provider-routing-model-options">
                <option value="local_stub" />
                <option value="mock" />
                <option value="fake-json-pro" />
                <option value="fake-chat-small" />
              </datalist>
              <label>
                Require JSON
                <input type="checkbox" checked={routingRequireJson} onChange={(event) => setRoutingRequireJson(event.target.checked)} />
              </label>
              <label>
                Require local only
                <input type="checkbox" checked={routingRequireLocalOnly} onChange={(event) => setRoutingRequireLocalOnly(event.target.checked)} />
              </label>
            </div>
            {routingPreview && (
              <div className="studio-grid compact-dashboard-grid">
                <DashboardCard title="Validation" value={routingPreview.validation.ok ? "ok" : "blocked"}>
                  <p>{[...routingPreview.validation.errors, ...routingPreview.validation.warnings].join(", ") || "No issues"}</p>
                </DashboardCard>
                <DashboardCard title="Selected" value={routingPreview.decision?.provider_id ?? "none"}>
                  <p>{routingPreview.decision ? `${routingPreview.decision.model_id} (${routingPreview.decision.reason})` : "No model selected"}</p>
                </DashboardCard>
                <DashboardCard title="Fallback" value={routingPreview.decision?.used_fallback ? "used" : "not used"}>
                  <p>Routing only returns metadata; provider factory remains the runtime entry.</p>
                </DashboardCard>
              </div>
            )}
            {modelAssignmentSummary ? (
              <>
                <div className="studio-grid compact-dashboard-grid">
                  <DashboardCard title="Assignment Validation" value={modelAssignmentSummary.validation_reports.every((report) => report.ok) ? "ok" : "blocked"}>
                    <p>{modelAssignmentSummary.warnings.join(", ") || "No global warnings"}</p>
                  </DashboardCard>
                  <DashboardCard title="Fallback Chains" value={String(Object.keys(modelAssignmentSummary.fallback_chains).length)}>
                    <p>Fallbacks are metadata only; Provider Gateway remains the only runtime entry.</p>
                  </DashboardCard>
                  <DashboardCard title="JSON Capability" value={routingUseCaseRequiresJson(routingUseCase) ? "required" : "optional"}>
                    <p>World intent parser and structured JSON assignments require JSON-capable models.</p>
                  </DashboardCard>
                </div>
                <ItemList
                  emptyText="No project model assignments saved."
                  items={modelAssignmentSummary.rules.map((rule) => (
                    <span key={`${rule.use_case}-${rule.primary_provider_id}-${rule.primary_model_id}`}>
                      {rule.use_case}: {rule.primary_provider_id}/{rule.primary_model_id}
                      {rule.fallback_provider_id ? ` -> ${rule.fallback_provider_id}/${rule.fallback_model_id}` : ""}
                      {modelAssignmentSummary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.length
                        ? ` (${modelAssignmentSummary.validation_reports.find((report) => report.rule.use_case === rule.use_case)?.warnings.join(", ")})`
                        : ""}
                    </span>
                  ))}
                />
              </>
            ) : routingSummary ? (
              <ItemList
                emptyText="No routing rules saved."
                items={routingSummary.rules.map((rule) => (
                  <span key={`${rule.use_case}-${rule.primary_provider_id}-${rule.primary_model_id}`}>
                    {rule.use_case}: {rule.primary_provider_id}/{rule.primary_model_id}
                    {rule.fallback_provider_id ? ` -> ${rule.fallback_provider_id}/${rule.fallback_model_id}` : ""}
                  </span>
                ))}
              />
            ) : (
              <p className="muted">Load or save local model assignments to see provider/model routes and fallback chains. No API keys are displayed.</p>
            )}
          </section>
          <div className="studio-columns">
            <section>
              <h4>Privacy Notes</h4>
              <ul className="compact-list">
                {summary.privacy_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </section>
            <section>
              <h4>Boundaries</h4>
              <ul className="compact-list">
                <li>GameState, saves, content packs, and memory stores are local files.</li>
                <li>LLM prompts only go to the configured provider layer.</li>
                <li>The frontend cannot edit .env or backend-sensitive configuration.</li>
                <li>Debug, authoring, playtest, eval, and perf data are studio-only surfaces.</li>
              </ul>
            </section>
          </div>
        </>
      ) : (
        <EmptyState title="Config summary unavailable." detail="The settings page stays empty if the safe summary endpoint fails." />
      )}
    </section>
  );
}

const PROVIDER_CONNECTIVITY_STATUSES = [
  "unconfigured",
  "configured_not_tested",
  "connected",
  "disconnected",
  "missing_secret",
  "invalid_base_url",
  "auth_failed",
  "model_list_failed",
  "unsupported_model_list",
  "timeout"
] as const;

const PROVIDER_MODEL_ASSIGNMENT_USE_CASES: Array<{ value: ProviderRoutingUseCase; label: string }> = [
  { value: "novel_draft", label: "Novel draft" },
  { value: "novel_rewrite", label: "Novel rewrite" },
  { value: "tavern_reply", label: "Tavern reply" },
  { value: "multi_npc_reply", label: "Multi-NPC reply" },
  { value: "world_intent_parse", label: "World intent parser" },
  { value: "world_narration", label: "World narrator" },
  { value: "memory_summary", label: "Memory summary" },
  { value: "cross_mode_draft", label: "Cross-Mode draft" },
  { value: "structured_json", label: "Structured JSON" },
  { value: "quality_eval", label: "Quality eval" },
  { value: "cheap_summary", label: "Cheap summary" }
];

function routingUseCaseRequiresJson(useCase: ProviderRoutingUseCase): boolean {
  return ["world_intent_parse", "structured_json", "cross_mode_draft", "quality_eval", "memory_summary"].includes(useCase);
}

function modelOptionsForProvider(profiles: ProviderProfileSummary[], providerId: string, currentModelId: string): string[] {
  const profile = profiles.find((item) => item.provider_profile_id === providerId);
  const modelIds = profile?.model_profiles.map((model) => model.model_id).filter(Boolean) ?? [];
  const options = new Set<string>(modelIds);
  if (currentModelId) options.add(currentModelId);
  if (options.size === 0) options.add(providerId || "local_stub");
  return Array.from(options);
}

function providerIdsForRouting(capabilities: ProviderCapabilityCatalog | null, currentProviderId: string): string[] {
  const options = new Set<string>((capabilities?.providers ?? []).map((provider) => provider.provider_id));
  if (currentProviderId) options.add(currentProviderId);
  if (options.size === 0) {
    options.add("local_stub");
    options.add("mock");
  }
  return Array.from(options);
}

function modelIdsForRouting(capabilities: ProviderCapabilityCatalog | null, providerId: string, currentModelId: string): string[] {
  const options = new Set<string>((capabilities?.models ?? []).filter((model) => model.provider_id === providerId).map((model) => model.model_id));
  if (currentModelId) options.add(currentModelId);
  if (options.size === 0) options.add(providerId || "local_stub");
  return Array.from(options);
}
type ProviderConnectivityStatus = (typeof PROVIDER_CONNECTIVITY_STATUSES)[number];

function ProviderConnectivityDashboard({
  profiles,
  matrix,
  statusById,
  lastTestedById,
  modelAssignmentOpen,
  onTestConnection,
  onFetchModels,
  onRefreshModels,
  onOpenModelAssignment,
  onOpenProviderSetup
}: {
  profiles: ProviderProfileSummary[];
  matrix: ProviderModelCapabilityMatrix | null;
  statusById: Record<string, Record<string, unknown>>;
  lastTestedById: Record<string, string>;
  modelAssignmentOpen: boolean;
  onTestConnection: (profileId: string) => void;
  onFetchModels: () => void;
  onRefreshModels: () => void;
  onOpenModelAssignment: () => void;
  onOpenProviderSetup: () => void;
}) {
  const rows = useMemo(() => profiles.map((profile) => buildProviderConnectivityRow(profile, matrix, statusById[profile.provider_profile_id], lastTestedById[profile.provider_profile_id])), [lastTestedById, matrix, profiles, statusById]);
  return (
    <section className="studio-section provider-connectivity-dashboard">
      <div className="authoring-pane-header">
        <div>
          <h4>Provider Connectivity Dashboard</h4>
          <p className="muted">Local Provider Gateway connectivity view. API keys, raw env, and Authorization headers are never displayed.</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={onFetchModels}>Fetch Models</button>
          <button type="button" onClick={onRefreshModels}>Refresh Models</button>
          <button type="button" onClick={onOpenModelAssignment}>Open Model Assignment</button>
          <button type="button" onClick={onOpenProviderSetup}>Open Provider Setup</button>
        </div>
      </div>
      {rows.length === 0 ? (
        <EmptyState title="No providers loaded." detail="Load or create local provider profiles. ProviderProfile stores api_key_env or secret_ref only, never plaintext keys." />
      ) : (
        <div className="debug-event-list">
          {rows.map((row) => (
            <details className="timeline-event provider-connectivity-row" key={row.providerId}>
              <summary>
                <span>{row.displayName}</span>
                <span>{row.providerType}</span>
                <ProviderConnectionStatusBadge status={row.connectionStatus} />
                <span>{row.modelCount} models</span>
              </summary>
              <dl className="event-details">
                <dt>Display name</dt><dd>{row.displayName}</dd>
                <dt>Provider type</dt><dd>{row.providerType}</dd>
                <dt>Connection status</dt><dd><ProviderConnectionStatusBadge status={row.connectionStatus} /></dd>
                <dt>Model count</dt><dd>{row.modelCount}</dd>
                <dt>Last tested</dt><dd>{row.lastTestedTime}</dd>
                <dt>Allowed modes</dt><dd>{row.allowedModes.join(", ") || "none"}</dd>
                <dt>Default model</dt><dd>{row.defaultModel}</dd>
                <dt>Warnings</dt><dd>{row.warnings.length ? row.warnings.map(redactReportText).join("; ") : "None"}</dd>
              </dl>
              <div className="button-row">
                <button type="button" onClick={() => onTestConnection(row.providerId)}>Test Connection</button>
                <button type="button" onClick={onFetchModels}>Fetch Models</button>
                <button type="button" onClick={onRefreshModels}>Refresh Models</button>
                <button type="button" onClick={onOpenModelAssignment}>Assign Models</button>
              </div>
            </details>
          ))}
        </div>
      )}
      {modelAssignmentOpen && (
        <section className="section-card">
          <h4>Provider Model Assignment by Mode</h4>
          <p className="muted">Assignment preview uses existing allowed_modes and recommended use cases. Persisted routing remains Provider Gateway configuration.</p>
          <div className="mode-landing-grid">
            {["Novel", "Tavern", "World", "Cross-Mode", "Quality"].map((mode) => {
              const modeId = mode.toLowerCase().replace("-", "_");
              const candidates = rows.filter((row) => row.allowedModes.map((item) => item.toLowerCase()).includes(modeId));
              return <FeatureCard key={mode} title={mode} detail={candidates.length ? candidates.map((candidate) => `${candidate.displayName}/${candidate.defaultModel}`).join(", ") : "No compatible model loaded."} />;
            })}
          </div>
        </section>
      )}
      <p className="muted">Relay is treated as OpenAI-compatible/custom base URL configuration, not an API resale service.</p>
    </section>
  );
}

function buildProviderConnectivityRow(
  profile: ProviderProfileSummary,
  matrix: ProviderModelCapabilityMatrix | null,
  status: Record<string, unknown> | undefined,
  lastTested: string | undefined
): {
  providerId: string;
  displayName: string;
  providerType: string;
  connectionStatus: ProviderConnectivityStatus;
  modelCount: number;
  lastTestedTime: string;
  allowedModes: string[];
  defaultModel: string;
  warnings: string[];
} {
  const matrixRows = matrix?.rows.filter((row) => row.provider_profile_id === profile.provider_profile_id) ?? [];
  const warnings = [...matrixRows.flatMap((row) => row.warnings), ...providerConnectivityWarnings(profile, matrixRows)];
  return {
    providerId: profile.provider_profile_id,
    displayName: redactReportText(profile.display_name),
    providerType: redactReportText(profile.provider_type),
    connectionStatus: providerConnectivityStatus(profile, status, matrixRows),
    modelCount: profile.model_profiles.length || matrixRows.length,
    lastTestedTime: lastTested ?? "not tested",
    allowedModes: profile.allowed_modes ?? sortedUnique(matrixRows.flatMap((row) => row.allowed_modes)),
    defaultModel: redactReportText(profile.model_profiles[0]?.model_id ?? matrixRows[0]?.model_id ?? "not assigned"),
    warnings
  };
}

function providerConnectivityStatus(profile: ProviderProfileSummary, status: Record<string, unknown> | undefined, matrixRows: ModelCapabilityMatrixRow[]): ProviderConnectivityStatus {
  if (!profile.enabled) return "unconfigured";
  if (profile.provider_type !== "mock" && profile.provider_type !== "local_stub" && !profile.api_key_env && !profile.secret_ref) return "missing_secret";
  if (profile.provider_type !== "mock" && profile.provider_type !== "local_stub" && profile.base_url_configured === false && profile.provider_type !== "openai") return "invalid_base_url";
  const serializedStatus = JSON.stringify(redactDebugText(status ?? {})).toLowerCase();
  if (!status) return "configured_not_tested";
  if (serializedStatus.includes("auth")) return "auth_failed";
  if (serializedStatus.includes("timeout")) return "timeout";
  if (serializedStatus.includes("disconnect") || serializedStatus.includes("failed")) return "disconnected";
  if (serializedStatus.includes("model_list_failed")) return "model_list_failed";
  if (matrixRows.length === 0 && profile.model_profiles.length === 0) return "unsupported_model_list";
  return "connected";
}

function providerConnectivityWarnings(profile: ProviderProfileSummary, matrixRows: ModelCapabilityMatrixRow[]): string[] {
  const warnings: string[] = [];
  if (!profile.enabled) warnings.push("Provider profile is disabled.");
  if (profile.provider_type !== "mock" && profile.provider_type !== "local_stub" && !profile.api_key_env && !profile.secret_ref) warnings.push("Missing secret reference or api_key_env.");
  if (profile.model_profiles.length === 0 && matrixRows.length === 0) warnings.push("No local model metadata loaded.");
  if (profile.provider_notes) warnings.push(redactReportText(profile.provider_notes));
  return warnings;
}

function formatDuration(value: number | undefined): string {
  return typeof value === "number" ? `${value.toFixed(1)}ms` : "n/a";
}

function formatStageDurations(stages: Record<string, number>): string {
  return Object.entries(stages)
    .slice(0, 4)
    .map(([stage, duration]) => `${stage} ${formatDuration(duration)}`)
    .join(", ");
}

function DashboardCard({
  title,
  value,
  children
}: {
  title: string;
  value: string;
  children: ReactNode;
}) {
  return (
    <section className="dashboard-card">
      <p className="muted">{title}</p>
      <strong>{value}</strong>
      <div>{children}</div>
    </section>
  );
}

function PageHeader({
  eyebrow,
  title,
  description,
  actions
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h2>{title}</h2>
        {description && <p className="muted">{description}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </header>
  );
}

function SectionCard({
  title,
  description,
  children,
  tone = "default"
}: {
  title: string;
  description?: string;
  children: ReactNode;
  tone?: "default" | "authoring" | "debug" | "player";
}) {
  return (
    <section className={`section-card ${tone}`}>
      <div className="section-card-header">
        <div>
          <h3>{title}</h3>
          {description && <p className="muted">{description}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

function ErrorPanel({ message, compact = false }: { message: string; compact?: boolean }) {
  if (!message) {
    return null;
  }
  return (
    <div className={`error-panel ${compact ? "compact" : ""}`} role="alert">
      <strong>Request failed</strong>
      <p>{sanitizeDisplayError(message)}</p>
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      {detail && <p>{detail}</p>}
    </div>
  );
}

function DisabledState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="disabled-state">
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}

function SafeSummaryCard({
  title,
  value,
  detail,
  children
}: {
  title: string;
  value: string;
  detail?: string;
  children?: ReactNode;
}) {
  return (
    <section className="safe-summary-card">
      <p className="muted">{title}</p>
      <strong>{value}</strong>
      {detail && <p>{detail}</p>}
      {children}
    </section>
  );
}

function FeatureCard({
  title,
  detail,
  action,
  status
}: {
  title: string;
  detail: string;
  action?: ReactNode;
  status?: ReactNode;
}) {
  return (
    <section className="feature-card">
      <div>
        <h4>{title}</h4>
        <p className="muted">{detail}</p>
      </div>
      {status && <div>{status}</div>}
      {action && <div className="feature-card-action">{action}</div>}
    </section>
  );
}

function ModeCard({
  title,
  detail,
  status,
  onOpen,
  disabled = false
}: {
  title: string;
  detail: string;
  status?: ReactNode;
  onOpen?: () => void;
  disabled?: boolean;
}) {
  return (
    <section className={`mode-card ${disabled ? "disabled" : ""}`}>
      <div>
        <h4>{title}</h4>
        <p>{detail}</p>
      </div>
      {status}
      {onOpen && (
        <button type="button" onClick={onOpen} disabled={disabled}>
          Open
        </button>
      )}
    </section>
  );
}

function LocalOnlyBadge() {
  return <span className="local-only-badge">Local-only</span>;
}

function RiskBadge({ level }: { level: "safe" | "warning" | "blocked" | "unknown" }) {
  return <span className={`risk-badge ${level}`}>{level}</span>;
}

function ValidationStatusBadge({ status }: { status: "passed" | "warning" | "failed" | "not_run" }) {
  return <span className={`validation-status-badge ${status}`}>{status.replace("_", " ")}</span>;
}

function SafeDebugNotice({ children }: { children?: ReactNode }) {
  return (
    <p className="muted">
      {children ?? "Debug data is local-only, redacted by default, and separated from normal player-facing UI."}
    </p>
  );
}

function EventTypeBadge({ type }: { type: string }) {
  return <span className="badge">{redactReportText(type || "event")}</span>;
}

function StateDeltaOpBadge({ op }: { op: string }) {
  return <span className="badge">{redactReportText(op || "op")}</span>;
}

function QualitySeverityBadge({ severity }: { severity: string }) {
  const normalized = severity.toLowerCase();
  const tone = normalized.includes("block") || normalized.includes("error") || normalized.includes("fail")
    ? "failed"
    : normalized.includes("warn") || normalized.includes("review")
      ? "warning"
      : normalized.includes("pass") || normalized.includes("clear")
        ? "passed"
        : "not_run";
  return <ValidationStatusBadge status={tone} />;
}

function LeakRiskBadge({ severity }: { severity: string }) {
  return <span className={`severity ${severity}`}>{redactReportText(severity)}</span>;
}

function ProviderConnectionStatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const enabled = ["connected", "configured", "available", "ok"].some((token) => normalized.includes(token));
  return <StatusBadge label={redactReportText(status || "provider unknown")} enabled={enabled} />;
}

function ModelCapabilityBadge({ label, supported }: { label: string; supported: boolean }) {
  return <span className={`badge ${supported ? "enabled" : "disabled"}`}>{label}: {supported ? "supported" : "unavailable"}</span>;
}

function TestRunStatusBadge({ status }: { status: string }) {
  return <QualitySeverityBadge severity={status} />;
}

function RedactedValue({ value = "[redacted]" }: { value?: string }) {
  return <span className="redacted-value">{sanitizeDisplayError(value)}</span>;
}

function SafeReportCard({ title, status, summary }: { title: string; status: string; summary: string }) {
  return (
    <section className="safe-summary-card safe-report-card">
      <p className="muted">{title}</p>
      <TestRunStatusBadge status={status} />
      <p>{redactReportText(summary)}</p>
    </section>
  );
}

function FilterToolbar({ children }: { children: ReactNode }) {
  return <div className="timeline-controls filter-toolbar">{children}</div>;
}

function moduleRiskBadgeLevel(level: string): "safe" | "warning" | "blocked" | "unknown" {
  if (level === "low" || level === "safe") {
    return "safe";
  }
  if (level === "blocked") {
    return "blocked";
  }
  if (level === "medium" || level === "high" || level === "warning") {
    return "warning";
  }
  return "unknown";
}

function moduleValidationBadgeStatus(status: string): "passed" | "warning" | "failed" | "not_run" {
  if (["valid", "passed", "ok", "compatible"].includes(status)) {
    return "passed";
  }
  if (["invalid", "failed", "blocked", "error"].includes(status)) {
    return "failed";
  }
  if (["warning", "warnings"].includes(status)) {
    return "warning";
  }
  return "not_run";
}

const DANGEROUS_MODULE_PERMISSIONS = [
  "execute_code",
  "access_filesystem",
  "access_network",
  "read_secrets",
  "write_database",
  "modify_game_state_directly",
  "bypass_visibility",
  "call_llm"
];

const AUTHORING_VALIDATION_CATEGORIES = [
  "world pack",
  "script pack",
  "character pack",
  "quest graph",
  "locations",
  "NPCs/factions/relationships",
  "items/economy",
  "rumors/crime/consequences",
  "action mods",
  "rule modules",
  "import/export"
];

const CERTIFICATION_LEVELS = [
  "safe_content",
  "safe_style",
  "verified_action",
  "experimental_rule_module",
  "unsafe_blocked"
];

function stringListFromUnknown(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)).filter(Boolean) : [];
}

function moduleSafePermissions(summary: ModulePermissionSummary | null): string[] {
  if (!summary) {
    return [];
  }
  return stringListFromUnknown(summary.permission_summary.safe_permissions);
}

function moduleRequestedPermissions(summary: ModulePermissionSummary | null): string[] {
  if (!summary) {
    return [];
  }
  return stringListFromUnknown(summary.permission_summary.requested_permissions);
}

function modulePermissionReason(permission: string, requested: boolean, dangerous: boolean): string {
  if (dangerous) {
    return requested
      ? `${permission} is requested and blocked by the local default-deny policy.`
      : `${permission} is dangerous and remains blocked unless a future audited sandbox exists.`;
  }
  return requested
    ? `${permission} is declarative metadata only and cannot execute package code.`
    : `${permission} is not requested by the selected package.`;
}

function SecretSafeNotice({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`secret-safe-notice ${compact ? "compact" : ""}`}>
      <strong>Secret-safe UI</strong>
      <p>
        API keys are not stored in project files. Provider secrets stay behind env or local secret
        resolver references, and normal export filters secrets, mature/private content, debug memory,
        and raw state deltas.
      </p>
    </div>
  );
}

function UnifiedNavigation({
  mode,
  requestedTool,
  hasProject,
  debugEnabled,
  debugOpen,
  onNavigate,
  onToggleDebug
}: {
  mode: AppMode;
  requestedTool: AuthoringToolId | null;
  hasProject: boolean;
  debugEnabled: boolean;
  debugOpen: boolean;
  onNavigate: (mode: AppMode, toolId?: AuthoringToolId) => void;
  onToggleDebug: () => void;
}) {
  const items: {
    label: string;
    targetMode: AppMode;
    toolId?: AuthoringToolId;
    active: boolean;
    disabled?: boolean;
    reason?: string;
    badge?: string;
  }[] = [
    { label: "Project Home", targetMode: "project", active: mode === "project" },
    { label: "Novel", targetMode: "project", active: mode === "project", badge: hasProject ? "Project Shell" : "Setup" },
    { label: "Tavern", targetMode: "project", active: mode === "project", badge: hasProject ? "Project Shell" : "Setup" },
    { label: "World", targetMode: "play", active: mode === "play" },
    { label: "Cross-Mode", targetMode: "project", active: mode === "project", badge: "Review" },
    {
      label: "Script / Mods",
      targetMode: "authoring",
      toolId: "advanced_modules",
      active: mode === "authoring" && (requestedTool === "advanced_modules" || requestedTool === "action_mods"),
      badge: "Local"
    },
    { label: "Providers", targetMode: "prompt_lab", active: mode === "prompt_lab" },
    { label: "Quality", targetMode: "studio", active: mode === "studio", badge: "Gate" },
    {
      label: "Settings",
      targetMode: "studio",
      active: mode === "studio",
      badge: "Privacy"
    }
  ];

  return (
    <nav className="unified-navigation" aria-label="Local studio navigation">
      <LocalOnlyBadge />
      <div className="nav-group">
        {items.map((item) => (
          <button
            key={`${item.label}-${item.toolId ?? item.targetMode}`}
            type="button"
            className={`nav-item ${item.active ? "active" : ""} ${item.disabled ? "disabled" : ""}`}
            onClick={() => onNavigate(item.targetMode, item.toolId)}
            disabled={item.disabled}
            title={item.reason}
          >
            <span>{item.label}</span>
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </button>
        ))}
        <button
          type="button"
          className={`nav-item debug-gated ${debugOpen ? "active" : ""}`}
          onClick={onToggleDebug}
          title={debugEnabled ? "Debug API enabled" : "Debug API disabled by ENABLE_DEBUG_API"}
        >
          <span>Debug / Replay</span>
          <span className="nav-badge">{debugEnabled ? "Enabled" : "Gated"}</span>
        </button>
      </div>
      <p className="muted nav-note">No account, no cloud sync, no online marketplace.</p>
    </nav>
  );
}

function LocalStatusBar({
  projectLoaded,
  backendStatus,
  providerStatus,
  qualityStatus,
  debugEnabled,
  apiKeyConfigured
}: {
  projectLoaded: boolean;
  backendStatus: string;
  providerStatus: string;
  qualityStatus: string;
  debugEnabled: boolean;
  apiKeyConfigured?: boolean;
}) {
  return (
    <section className="local-status-bar" aria-label="Local status">
      <StatusBadge label={projectLoaded ? "Project loaded" : "No project"} enabled={projectLoaded} />
      <StatusBadge label={`Backend ${backendStatus}`} enabled={backendStatus === "ok" || backendStatus === "available"} />
      <StatusBadge label={providerStatus ? `Provider ${providerStatus}` : "Provider missing"} enabled={Boolean(providerStatus && providerStatus !== "missing")} />
      <StatusBadge label={`Quality ${qualityStatus}`} enabled={qualityStatus !== "not run"} />
      <StatusBadge label={debugEnabled ? "Debug enabled" : "Debug disabled"} enabled={debugEnabled} />
      <StatusBadge label="Local-only" enabled />
      <StatusBadge label={apiKeyConfigured ? "Secret ref configured" : "No key in project"} enabled />
    </section>
  );
}

function SafePathSummary({ value }: { value?: string | null }) {
  const safeValue = value?.trim() || "Safe path summary unavailable";
  return <span className="safe-path-summary" title="Safe path summary; full sensitive paths are not shown in normal UI.">{safeValue}</span>;
}

function LocalLauncherStatusPanel({
  status,
  config,
  startupChecks,
  error,
  onRefresh,
  onNavigate
}: {
  status: LocalStudioStatus | null;
  config: LocalStudioConfigSummary | null;
  startupChecks: LocalStudioStartupChecks | null;
  error: string;
  onRefresh: () => void;
  onNavigate: (mode: AppMode, toolId?: AuthoringToolId) => void;
}) {
  return (
    <SectionCard title="Local Launcher / Startup Status" description="Safe local desktop startup summary. No API keys, raw env, sensitive paths, hidden facts, or debug state are shown.">
      <div className="section-heading-row">
        <div>
          <h4>Startup Status</h4>
          <p className="muted">Backend health, config state, Provider profile count, Quality API, Debug, and local-only boundary.</p>
        </div>
        <button type="button" onClick={onRefresh}>Refresh Status</button>
      </div>
      <ErrorPanel message={error} compact />
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Backend" value={status?.backend_running ? "running" : "unavailable"} detail={`App ${status?.app_version ?? "unknown"}`} />
        <SafeSummaryCard title="Frontend" value="local UI" detail="Vite/desktop surface calls local backend APIs only." />
        <SafeSummaryCard title="Project root" value={status?.project_root_configured ? "configured" : "missing"} detail={status?.current_workspace?.path_redacted ?? "Safe path summary unavailable"} />
        <SafeSummaryCard title="SQLite / Database" value={status?.database_configured ? "configured" : "missing"} detail="Connection string is never displayed." />
        <SafeSummaryCard title="Workspace" value={status?.current_workspace?.safe_status ?? "not selected"} detail={status?.current_workspace?.path_redacted ?? "Safe path summary unavailable"} />
        <SafeSummaryCard title="Logs" value="redacted" detail="Local logs are read as safe summaries from ignored log directories." />
        <SafeSummaryCard title="Provider profiles" value={String(status?.provider_profiles_count ?? 0)} detail={`${status?.provider_secrets_configured_count ?? 0} secret reference(s) configured; values hidden.`} />
        <SafeSummaryCard title="Debug" value={status?.debug_enabled ? "enabled" : "disabled"} detail="Debug views remain gated by ENABLE_DEBUG_API." />
        <SafeSummaryCard title="Quality API" value={status?.quality_api_enabled ? "available" : "not available"} detail="Quality reports are local safe summaries." />
      </div>
      <div className="quick-actions">
        <button type="button" onClick={onRefresh}>Retry Health Check</button>
        <button type="button" onClick={() => onNavigate("project")}>Project Picker</button>
        <button type="button" onClick={() => onNavigate("studio")}>Open Local Config Wizard</button>
        <button type="button" onClick={() => onNavigate("prompt_lab")}>Open Provider Setup Wizard</button>
        <button type="button" onClick={() => onNavigate("studio")}>View Local Logs</button>
      </div>
      {startupChecks ? (
        <div className="desktop-health-list">
          {startupChecks.checks.map((check) => (
            <article className={`desktop-health-item ${check.status}`} key={check.check_id}>
              <div className="section-heading-row">
                <strong>{check.label}</strong>
                <span className={`status-pill ${check.status}`}>{check.status}</span>
              </div>
              <p>{check.safe_summary}</p>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No startup checks loaded." detail="Refresh the startup status to load safe local checks." />
      )}
      {config && (
        <p className="muted">
          Local Config Wizard summary: provider profiles {config.provider_profiles_count}, module API {config.module_api_enabled ? "enabled" : "disabled"}, authoring {config.authoring_enabled ? "enabled" : "disabled"}.
        </p>
      )}
      <SecretSafeNotice compact />
    </SectionCard>
  );
}

function ProjectHomeRedesignPanel({
  status,
  selectedProjectId,
  configSummary,
  worldHealth,
  recentSaves,
  validationSummaries,
  onNavigate
}: {
  status: StudioStatus | null;
  selectedProjectId: string;
  configSummary: StudioConfigSummary | null;
  worldHealth: WorldHealthScore | null;
  recentSaves: SaveSummary[];
  validationSummaries: { world_id: string; ok: boolean; error_count?: number; warning_count?: number }[];
  onNavigate: (mode: AppMode, toolId?: AuthoringToolId) => void;
}) {
  const providerConfigured = Boolean(configSummary?.api_key_configured || configSummary?.provider_status === "configured");
  const qualityStatus = worldHealth ? "available" : "not run";
  return (
    <SectionCard
      title="Project Home"
      description="A local-first overview for project status, mode entry, providers, quality, and privacy."
    >
      <div className="project-home-hero">
        <div>
          <p className="eyebrow">Local UI / UX Foundation</p>
          <h3>{selectedProjectId || "Local Narrative Project"}</h3>
          <p className="muted">
            AI Narrative Studio stays local-first: no account, No cloud sync, and No online marketplace.
          </p>
        </div>
        <LocalOnlyBadge />
      </div>
      <div className="mode-landing-grid">
        <ModeCard title="Novel" detail="Manuscripts, outlines, chapters, scenes, exports, and World to Novel drafts." onOpen={() => onNavigate("project")} status={<ValidationStatusBadge status="not_run" />} />
        <ModeCard title="Tavern" detail="Characters, sessions, RP memory, multi-NPC scenes, mood, voice, and safety settings." onOpen={() => onNavigate("project")} status={<RiskBadge level="safe" />} />
        <ModeCard title="World" detail="Continue local play, inspect visible state, saves, quests, inventory, and replay." onOpen={() => onNavigate("play")} status={<StatusBadge label={status?.worlds_count ? "Worlds available" : "No world loaded"} enabled={Boolean(status?.worlds_count)} />} />
        <ModeCard title="Script / Mods" detail="Local packages, permissions, compatibility, certification, and quality gates." onOpen={() => onNavigate("authoring", "advanced_modules")} status={<RiskBadge level="unknown" />} />
        <ModeCard title="Providers" detail="Configure provider profiles by env or secret reference only. No plaintext key field." onOpen={() => onNavigate("prompt_lab")} status={<StatusBadge label={providerConfigured ? "Configured" : "Missing"} enabled={providerConfigured} />} />
        <ModeCard title="Quality" detail="World health, narrative evals, playtests, compatibility, and release confidence." onOpen={() => onNavigate("studio")} status={<ValidationStatusBadge status={worldHealth ? "passed" : "not_run"} />} />
        <ModeCard title="Debug / Replay" detail="Timeline and diagnostics remain gated by ENABLE_DEBUG_API." onOpen={() => onNavigate("play")} status={<StatusBadge label={status?.debug_api_enabled ? "Debug enabled" : "Debug gated"} enabled={status?.debug_api_enabled} />} />
        <ModeCard title="Settings" detail="Local privacy, provider, export, debug, mature module, UI, and quality preferences." onOpen={() => onNavigate("studio")} status={<LocalOnlyBadge />} />
      </div>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Recent activity" value={recentSaves.length ? `${recentSaves.length} recent saves` : "No recent saves"} detail="Shown as safe save summaries only." />
        <SafeSummaryCard title="Validation" value={validationSummaries.length ? `${validationSummaries.length} worlds checked` : "Not run"} detail={validationSummaries.some((item) => !item.ok) ? "Some worlds need review." : "No blocker summary available."} />
        <SafeSummaryCard title="Privacy summary" value="Secrets filtered" detail="API key not stored in project; export filters secrets; cloud sync disabled / not implemented." />
      </div>
      <div className="quick-actions">
        <button type="button" onClick={() => onNavigate("project")}>Open Novel</button>
        <button type="button" onClick={() => onNavigate("project")}>Open Tavern</button>
        <button type="button" onClick={() => onNavigate("play")}>Open World</button>
        <button type="button" onClick={() => onNavigate("studio")}>Run Quality Gate</button>
        <button type="button" onClick={() => onNavigate("studio")}>Open Settings</button>
        <button type="button" onClick={() => onNavigate("prompt_lab")}>Open Providers</button>
      </div>
      <SecretSafeNotice />
    </SectionCard>
  );
}

function LocalHelpOnboardingPanel() {
  return (
    <SectionCard title="Offline Help Center / Local Help / Onboarding" description="Short guide to the local-first workflow. Content is bundled locally and does not load remote docs.">
      <div className="mode-landing-grid">
        <FeatureCard title="Getting Started" detail="Create or open a local project, choose a mode, and run Quality Gate before release." />
        <FeatureCard title="What is AI Narrative Studio" detail="A local writing, Tavern RP, and World Studio workspace sharing one fact boundary." />
        <FeatureCard title="Local-first workflow" detail="No account, no cloud sync, no online marketplace, and API keys stay local." />
        <FeatureCard title="Project Picker" detail="Open recent local projects with redacted path summaries; no cloud project registry." />
        <FeatureCard title="Novel / Tavern / World modes" detail="Draft prose, roleplay safely, and play the world without letting UI bypass rules." />
        <FeatureCard title="Cross-Mode proposals" detail="Drafts and proposals are reviewed before becoming world changes." />
        <FeatureCard title="Provider setup" detail="Use api_key_env or secret_ref; never paste plaintext API keys into the frontend." />
        <FeatureCard title="Mods and permissions" detail="Local packages are validated, never executed as arbitrary code." />
        <FeatureCard title="Quality Gate" detail="Run deterministic checks for leaks, migration, compatibility, and release readiness." />
        <FeatureCard title="Backup / Restore" detail="Dry-run first; .env, API keys, logs/cache/build outputs, debug and mature/private content are excluded by default." />
        <FeatureCard title="Diagnostics / Logs" detail="Local diagnostics and logs are redacted and never uploaded." />
        <FeatureCard title="Privacy and secrets" detail="Exports and diagnostics default to filtered safe summaries." />
        <FeatureCard title="Desktop Packaging" detail="Packaging excludes .env, databases, logs/cache, node_modules, frontend/dist, desktop build outputs, backups, crash reports, and diagnostics bundles." />
        <FeatureCard title="Mature Module default off" detail="Mature/private content stays disabled and excluded unless explicit local policy allows it." />
      </div>
    </SectionCard>
  );
}

function FirstRunOnboardingFlow({
  hasProject,
  onOpenProjectHome,
  onOpenProviderSetup,
  onSkip,
  onComplete
}: {
  hasProject: boolean;
  onOpenProjectHome: () => void;
  onOpenProviderSetup: () => void;
  onSkip: () => void;
  onComplete: () => void;
}) {
  const [step, setStep] = useState<number>(0);
  const steps = [
    "Welcome / local-first explanation",
    "Create or open project",
    "Configure provider profile or skip",
    "Privacy/secrets explanation",
    "Open Project Home",
  ];
  return (
    <SectionCard title="First-Run Onboarding" description="A local-only startup guide. No account needed, no cloud sync, and Provider setup can be skipped.">
      <div className="safe-summary-grid">
        <SafeSummaryCard title="No account needed" value="local" detail="The app runs against local backend APIs." />
        <SafeSummaryCard title="No cloud sync" value="disabled" detail="Projects are not uploaded or synchronized." />
        <SafeSummaryCard title="API keys stay local" value="secret ref only" detail="Use api_key_env or secret_ref in Provider Setup." />
        <SafeSummaryCard title="World boundary" value="protected" detail="Onboarding never modifies GameState." />
      </div>
      <ol className="compact-list">
        {steps.map((label, index) => (
          <li key={label}>
            <strong>{index === step ? "Current: " : ""}{label}</strong>
          </li>
        ))}
      </ol>
      {step === 0 && <p>Welcome to AI Narrative Studio. This is a local-first Novel, Tavern RP, and World Studio workspace.</p>}
      {step === 1 && <p>{hasProject ? "A local project/workspace is already selected." : "Open Project Picker to create or select a local project. Paths are shown as safe summaries."}</p>}
      {step === 2 && <p>Provider setup is optional. You can skip it and use mock/local_stub. Do not paste plaintext API keys into the frontend.</p>}
      {step === 3 && <p>Exports, backups, diagnostics, and logs filter secrets, hidden/debug data, and mature/private content by default.</p>}
      {step === 4 && <p>Open Project Home when you are ready. You can revisit local help from the dashboard.</p>}
      <div className="quick-actions">
        <button type="button" onClick={() => setStep(Math.max(0, step - 1))} disabled={step === 0}>Back</button>
        <button type="button" onClick={() => setStep(Math.min(steps.length - 1, step + 1))} disabled={step === steps.length - 1}>Next</button>
        <button type="button" onClick={onOpenProjectHome}>Open Project Home</button>
        <button type="button" onClick={onOpenProviderSetup}>Provider Setup Wizard</button>
        <button type="button" onClick={onSkip}>Skip onboarding</button>
        <button type="button" onClick={onComplete}>Finish</button>
      </div>
      <p className="muted">Onboarding state is stored locally as completed/skipped only; it contains no secrets, raw env, project paths, or provider credentials.</p>
    </SectionCard>
  );
}

function ModeLandingPage({
  title,
  localStatus,
  features,
  warnings,
  actions
}: {
  title: string;
  localStatus: string;
  features: string[];
  warnings: string[];
  actions: string[];
}) {
  return (
    <section className="mode-landing-page">
      <div className="mode-landing-header">
        <h3>{title}</h3>
        <LocalOnlyBadge />
      </div>
      <p className="muted">{localStatus}</p>
      <h4>Available</h4>
      <ItemList emptyText="No features configured." items={features.map((feature) => <span key={feature}>{feature}</span>)} />
      <h4>Warnings</h4>
      <ItemList emptyText="No warnings." items={warnings.map((warning) => <span key={warning}>{warning}</span>)} />
      <h4>Quick actions</h4>
      <div className="quick-actions">
        {actions.map((action) => (
          <button type="button" key={action} disabled>{action}</button>
        ))}
      </div>
    </section>
  );
}

function DiagnosticsExportPanel({
  selectedProjectId,
  status,
  configSummary,
  localConfigSummary,
  worldHealth,
  desktopHealth,
  safeErrors
}: {
  selectedProjectId: string;
  status: StudioStatus | null;
  configSummary: StudioConfigSummary | null;
  localConfigSummary: LocalConfigSummary | null;
  worldHealth: WorldHealthScore | null;
  desktopHealth: DesktopHealthCheckReport | null;
  safeErrors: string[];
}) {
  const [includeDebug, setIncludeDebug] = useState(false);
  const [confirmedDebug, setConfirmedDebug] = useState(false);
  const debugAllowed = Boolean(status?.debug_api_enabled);
  const diagnostics = {
    project: {
      project_id: selectedProjectId || "not_selected",
      local_only: true,
      cloud_sync: "not_implemented"
    },
    provider: {
      provider_status: configSummary?.provider_status ?? "unknown",
      provider_type: localConfigSummary?.provider_type ?? "unknown",
      api_key_status: "[redacted]"
    },
    quality: {
      world_health: worldHealth ? "available" : "not_run",
      desktop_health: desktopHealth ? desktopHealth.overall_status : "not_run"
    },
    modules: {
      status: "safe summary only"
    },
    recent_safe_errors: safeErrors.map((item) => sanitizeDisplayError(item)).slice(0, 5),
    filters: [
      "API key",
      ".env",
      "provider secrets",
      "hidden facts",
      "mature/private content",
      "debug memory",
      "raw state_deltas"
    ],
    debug_export: includeDebug && confirmedDebug && debugAllowed ? "explicitly_requested" : "excluded"
  };

  function downloadDiagnostics() {
    if (includeDebug && (!debugAllowed || !confirmedDebug)) {
      return;
    }
    const blob = new Blob([JSON.stringify(diagnostics, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "ai-narrative-studio-diagnostics-safe.json";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <SectionCard
      title="Diagnostics Export"
      description="Local-only safe JSON preview. Nothing is uploaded."
    >
      <SecretSafeNotice compact />
      <FilterToolbar>
        <label>
          <input
            type="checkbox"
            checked={includeDebug}
            onChange={(event) => {
              setIncludeDebug(event.target.checked);
              setConfirmedDebug(false);
            }}
          />
          Include debug export metadata
        </label>
        {includeDebug && (
          <label>
            <input
              type="checkbox"
              checked={confirmedDebug}
              disabled={!debugAllowed}
              onChange={(event) => setConfirmedDebug(event.target.checked)}
            />
            I understand debug export requires ENABLE_DEBUG_API and explicit confirmation.
          </label>
        )}
        {!debugAllowed && includeDebug && (
          <DisabledState
            title="Debug export gated"
            detail="ENABLE_DEBUG_API is disabled, so diagnostics remain normal safe summaries only."
          />
        )}
      </FilterToolbar>
      <SafeJSON value={diagnostics} />
      <button type="button" onClick={downloadDiagnostics} disabled={includeDebug && (!debugAllowed || !confirmedDebug)}>
        Export local diagnostics JSON
      </button>
    </SectionCard>
  );
}

function DiagnosticsBundlePanel({
  preview,
  createResult,
  error,
  debugEnabled,
  onPreview,
  onCreate
}: {
  preview: DiagnosticsBundlePreview | null;
  createResult: DiagnosticsBundleCreateResponse | null;
  error: string;
  debugEnabled: boolean;
  onPreview: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
  onCreate: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
}) {
  const [includeDebug, setIncludeDebug] = useState(false);
  const [confirmedDebug, setConfirmedDebug] = useState(false);
  const includedSections = normalizeDiagnosticsSections(preview?.manifest.included_sections, DIAGNOSTICS_INCLUDED_SECTIONS);
  const excludedSections = normalizeDiagnosticsSections(preview?.manifest.excluded_sections, DIAGNOSTICS_EXCLUDED_SECTIONS);
  const redactedLogCount = countDiagnosticsPayloadItems(preview?.safe_payload, "redacted_logs");
  const recentErrorCount = countDiagnosticsPayloadItems(preview?.safe_payload, "recent_safe_errors");
  const canCreate = !includeDebug || (debugEnabled && confirmedDebug);

  return (
    <SectionCard title="Diagnostics Bundle Review UI" description="Diagnostics Bundle UI preview before writing it. Default bundle excludes secrets, hidden/debug, mature/private, databases, raw logs, and raw state. Nothing is uploaded.">
      <div className="section-heading-row">
        <div>
          <h4>Diagnostics Preview</h4>
          <p className="muted">Review included sections, excluded sections, redaction status, and debug bundle gating before creating a local zip.</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => onPreview(includeDebug, confirmedDebug)}>Preview Bundle</button>
          <button type="button" onClick={() => onCreate(includeDebug, confirmedDebug)} disabled={!canCreate}>Create Diagnostics Bundle</button>
        </div>
      </div>
      <FilterToolbar>
        <label>
          <input
            type="checkbox"
            checked={includeDebug}
            onChange={(event) => {
              setIncludeDebug(event.target.checked);
              setConfirmedDebug(false);
            }}
          />
          Request debug bundle metadata
        </label>
        {includeDebug && (
          <label>
            <input
              type="checkbox"
              checked={confirmedDebug}
              disabled={!debugEnabled}
              onChange={(event) => setConfirmedDebug(event.target.checked)}
            />
            I confirm debug bundle export. It requires ENABLE_DEBUG_API and may include internal state summaries.
          </label>
        )}
      </FilterToolbar>
      {includeDebug && !debugEnabled && (
        <DisabledState title="Debug bundle gated" detail="ENABLE_DEBUG_API is disabled, so diagnostics creation remains normal safe summaries only." />
      )}
      <ErrorPanel message={error} compact />
      {preview ? (
        <>
          <div className="safe-summary-grid">
            <SafeSummaryCard title="Bundle" value={preview.manifest.bundle_id} detail={preview.writes_file ? "writes file" : "preview only"} />
            <SafeSummaryCard title="Redaction" value={preview.manifest.contains_secrets ? "blocked" : "applied"} detail={preview.manifest.redaction_policy} />
            <SafeSummaryCard title="Debug/private" value={preview.manifest.contains_hidden_debug_mature_private ? "blocked" : "excluded"} detail={preview.manifest.debug_bundle ? "debug explicitly confirmed" : "normal safe bundle"} />
            <SafeSummaryCard title="Recent redacted errors" value={String(recentErrorCount)} detail="Safe summaries only." />
            <SafeSummaryCard title="Redacted logs" value={String(redactedLogCount)} detail="Raw logs with secrets are never shown here." />
            <SafeSummaryCard title="Upload" value="never" detail="Diagnostics bundle review is local-only." />
          </div>
          <div className="grid two-column">
            <div>
              <h4>Included sections</h4>
              <ItemList emptyText="No included sections." items={includedSections.map((section) => <span key={section}>{section}</span>)} />
            </div>
            <div>
              <h4>Excluded sections</h4>
              <ItemList emptyText="No exclusions listed." items={excludedSections.map((section) => <span key={section}>{section}</span>)} />
            </div>
          </div>
          <details>
            <summary>Safe payload preview</summary>
            <SafeJSON value={buildDiagnosticsSafePayloadPreview(preview.safe_payload)} />
          </details>
          <ItemList emptyText="No diagnostics warnings." items={preview.warnings.map((warning) => <span key={warning}>{sanitizeDisplayError(warning)}</span>)} />
          {createResult && (
            <SuccessPanel
              compact
              message={`Diagnostics bundle created locally: ${createResult.bundle_path_summary ?? createResult.manifest.bundle_id}. No upload was performed.`}
            />
          )}
        </>
      ) : (
        <EmptyState title="No diagnostics bundle preview." detail="Preview creates a safe manifest without writing files." />
      )}
    </SectionCard>
  );
}

const DIAGNOSTICS_INCLUDED_SECTIONS = [
  "app summary",
  "project safe summary",
  "provider safe summary",
  "quality summary",
  "module status",
  "recent redacted errors",
  "redacted logs"
];

const DIAGNOSTICS_EXCLUDED_SECTIONS = [
  ".env",
  "API key",
  "provider secrets",
  "raw env",
  "raw prompt/output",
  "hidden facts",
  "NPC secrets",
  "debug memory",
  "raw state_deltas",
  "mature/private",
  "database files"
];

function normalizeDiagnosticsSections(sections: string[] | undefined, fallback: string[]): string[] {
  const existing = new Set((sections ?? []).map((section) => section.replace(/_/g, " ").replace(/ content$/i, "").trim()));
  fallback.forEach((section) => existing.add(section));
  return Array.from(existing).filter(Boolean);
}

function countDiagnosticsPayloadItems(payload: Record<string, unknown> | undefined, key: string): number {
  const value = payload?.[key];
  if (Array.isArray(value)) {
    return value.length;
  }
  if (value && typeof value === "object") {
    return Object.keys(value).length;
  }
  return value ? 1 : 0;
}

function buildDiagnosticsSafePayloadPreview(payload: Record<string, unknown>): Record<string, unknown> {
  return {
    app_summary: payload.app_summary ?? payload.app_version ?? "safe summary",
    project_safe_summary: payload.project_safe_summary ?? "safe summary",
    provider_safe_summary: payload.provider_safe_summary ?? "configured/missing only",
    quality_summary: payload.quality_summary ?? "safe counts only",
    module_status: payload.module_status_summary ?? "safe module status only",
    recent_redacted_errors: countDiagnosticsPayloadItems(payload, "recent_safe_errors"),
    redacted_logs: countDiagnosticsPayloadItems(payload, "redacted_logs"),
    excluded_raw_sections: DIAGNOSTICS_EXCLUDED_SECTIONS
  };
}

function LocalTestRunDashboard({
  diagnosticsBundlePreview,
  worldHealth,
  narrativeEvalReports,
  playtestReports,
  scenarioRegressionRuns,
  performanceSummary,
  contentCoverage
}: {
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  playtestReports: PlaytestReport[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  performanceSummary: DebugPerformanceSummaryResponse | null;
  contentCoverage: ContentCoverageReport | null;
}) {
  const recommendedCommands = [
    "python -m pytest",
    "cd frontend && npm.cmd run build",
    "python -m pytest backend/tests/test_v35_provider_connection_test_backend.py backend/tests/test_v35_provider_model_discovery_sync.py",
    "$env:PYTHONPATH='backend'; python -m app.tools.validate_world mist_valley",
    "python -m backend.app.tools.quality_gate --world mist_valley"
  ];
  const safeReports = buildLocalTestSafeReports({
    diagnosticsBundlePreview,
    worldHealth,
    narrativeEvalReports,
    playtestReports,
    scenarioRegressionRuns,
    performanceSummary,
    contentCoverage
  });
  const frontendBuildStatus = performanceSummary ? "local metrics available" : "run build locally";

  return (
    <SectionCard title="Local Test Run Dashboard" description="Read-only local verification guide. This UI does not execute arbitrary shell commands, upload results, show raw env, or modify GameState.">
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Local-only" value="yes" detail="Commands run outside this UI in your local shell." />
        <SafeReportCard title="Frontend build status" status={frontendBuildStatus} summary="Use the recommended build command for authoritative result." />
        <SafeSummaryCard title="Latest safe reports" value={String(safeReports.filter((report) => report.status !== "not run").length)} detail="Derived from local QA summaries already loaded in the app." />
        <SafeReportCard title="Shell execution" status="blocked" summary="No arbitrary command input or terminal is exposed." />
      </div>
      <div className="grid two-column">
        <div>
          <h4>Recommended commands</h4>
          <ItemList
            emptyText="No recommended commands."
            items={recommendedCommands.map((command) => (
              <code key={command}>{command}</code>
            ))}
          />
          <p className="muted">provider/model discovery tests use fake provider or fake client. CI must not call real providers.</p>
        </div>
        <div>
          <h4>Latest safe test report</h4>
          <ItemList
            emptyText="No local QA reports loaded yet."
            items={safeReports.map((report) => (
              <span key={report.label}>
                <strong>{report.label}</strong>: <TestRunStatusBadge status={report.status} /> · {report.safeSummary}
              </span>
            ))}
          />
        </div>
      </div>
      <div className="mode-landing-grid">
        <FeatureCard title="Pytest" detail="Run the full backend suite locally. Output should stay redacted and use mock/local_stub providers." status={<ValidationStatusBadge status="not_run" />} />
        <FeatureCard title="Frontend build" detail="Run Vite/TypeScript build locally. The dashboard does not execute npm or shell commands." status={<ValidationStatusBadge status="not_run" />} />
        <FeatureCard title="Quality gate tools" detail="Use local quality gate tools for world, module, provider, and release readiness checks." status={<ValidationStatusBadge status={worldHealth ? "passed" : "not_run"} />} />
        <FeatureCard title="No arbitrary command UI" detail="No generic terminal, no custom shell input, no upload, no secrets, no raw env." status={<ValidationStatusBadge status="passed" />} />
      </div>
    </SectionCard>
  );
}

function buildLocalTestSafeReports({
  diagnosticsBundlePreview,
  worldHealth,
  narrativeEvalReports,
  playtestReports,
  scenarioRegressionRuns,
  performanceSummary,
  contentCoverage
}: {
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  playtestReports: PlaytestReport[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  performanceSummary: DebugPerformanceSummaryResponse | null;
  contentCoverage: ContentCoverageReport | null;
}): Array<{ label: string; status: string; safeSummary: string }> {
  return [
    {
      label: "World quality",
      status: worldHealth ? (worldHealth.blockers.length ? "blocked" : "loaded") : "not run",
      safeSummary: worldHealth ? `${worldHealth.blockers.length} blockers, ${worldHealth.warnings.length} warnings` : "Run local quality gate."
    },
    {
      label: "Novel quality",
      status: narrativeEvalReports.length ? "loaded" : "not run",
      safeSummary: `${narrativeEvalReports.length} safe report(s) loaded.`
    },
    {
      label: "Playtest",
      status: playtestReports.length ? "loaded" : "not run",
      safeSummary: `${playtestReports.length} local playtest report(s); no real provider required.`
    },
    {
      label: "Scenario regression",
      status: scenarioRegressionRuns.length ? "loaded" : "not run",
      safeSummary: `${scenarioRegressionRuns.length} regression run(s) loaded.`
    },
    {
      label: "Diagnostics preview",
      status: diagnosticsBundlePreview ? "previewed" : "not run",
      safeSummary: diagnosticsBundlePreview ? `${diagnosticsBundlePreview.manifest.included_sections.length} included, ${diagnosticsBundlePreview.manifest.excluded_sections.length} excluded.` : "Preview diagnostics bundle before release."
    },
    {
      label: "Performance metrics",
      status: performanceSummary ? "loaded" : "not run",
      safeSummary: performanceSummary ? `${performanceSummary.sample_count} local sample(s).` : "Performance dashboard can show local samples when debug API is available."
    },
    {
      label: "Content coverage",
      status: contentCoverage ? "loaded" : "not run",
      safeSummary: contentCoverage ? `${contentCoverage.locations.covered}/${contentCoverage.locations.total} locations, ${contentCoverage.quests.covered}/${contentCoverage.quests.total} quests covered.` : "Run coverage tools when preparing release."
    }
  ];
}

const SAFE_DEBUG_EXPORT_SCOPES = [
  { id: "eventlog_debug", label: "EventLog debug", rawRisk: true },
  { id: "statedelta_debug", label: "StateDelta debug", rawRisk: true },
  { id: "visibility_compare_report", label: "visibility compare report", rawRisk: false },
  { id: "module_debug_summary", label: "module debug summary", rawRisk: false },
  { id: "provider_diagnostics_safe_summary", label: "provider diagnostics safe summary", rawRisk: false }
];

function SafeDebugExportWizard({
  debugEnabled,
  diagnosticsPreview,
  diagnosticsCreateResult,
  error,
  onPreview,
  onCreate
}: {
  debugEnabled: boolean;
  diagnosticsPreview: DiagnosticsBundlePreview | null;
  diagnosticsCreateResult: DiagnosticsBundleCreateResponse | null;
  error: string;
  onPreview: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
  onCreate: (includeDebug: boolean, explicitConfirmDebug: boolean) => void;
}) {
  const [selectedScopes, setSelectedScopes] = useState<string[]>(["visibility_compare_report", "module_debug_summary", "provider_diagnostics_safe_summary"]);
  const [confirmRawExport, setConfirmRawExport] = useState(false);
  const selectedRawScopes = SAFE_DEBUG_EXPORT_SCOPES.filter((scope) => selectedScopes.includes(scope.id) && scope.rawRisk);
  const rawExportRequested = selectedRawScopes.length > 0;
  const canPreview = debugEnabled && (!rawExportRequested || confirmRawExport);
  const canCreate = debugEnabled && (!rawExportRequested || confirmRawExport);

  function toggleScope(scopeId: string) {
    setSelectedScopes((current) =>
      current.includes(scopeId) ? current.filter((item) => item !== scopeId) : [...current, scopeId]
    );
  }

  return (
    <SectionCard title="Safe Debug Export Wizard" description="Local-only debug export review. Debug exports require ENABLE_DEBUG_API and explicit confirmation. Defaults stay on safe summaries.">
      <div className="safe-summary-grid">
        <SafeSummaryCard title="ENABLE_DEBUG_API" value={debugEnabled ? "enabled" : "disabled"} detail={debugEnabled ? "Debug export can be previewed with confirmation." : "Debug export disabled until local debug API is enabled."} />
        <SafeSummaryCard title="Raw exports" value={rawExportRequested ? "requested" : "not selected"} detail={rawExportRequested ? "Explicit confirm required before preview/create." : "Safe summaries only."} />
        <SafeSummaryCard title="Redaction policy" value={diagnosticsPreview?.manifest.redaction_policy ?? "desktop_safe_redaction"} detail="API keys, provider secrets, raw env, and sensitive provider errors are redacted." />
        <SafeSummaryCard title="Upload" value="never" detail="Debug export is local-only and never uploaded." />
      </div>
      {!debugEnabled && <DisabledState title="Debug export disabled" detail="ENABLE_DEBUG_API is false. Safe debug export preview/create is unavailable." />}
      <SafeDebugNotice>Risk warning: raw debug materials can include internal state summaries. They must not include API keys, raw env, provider secrets, or hidden/mature/private content by default.</SafeDebugNotice>
      <div className="mode-landing-grid">
        {SAFE_DEBUG_EXPORT_SCOPES.map((scope) => (
          <label key={scope.id} className="feature-card checkbox-row">
            <input
              type="checkbox"
              checked={selectedScopes.includes(scope.id)}
              onChange={() => toggleScope(scope.id)}
              disabled={!debugEnabled}
            />
            <span>
              <strong>{scope.label}</strong>
              <small>{scope.rawRisk ? "raw debug scope, explicit confirm required" : "safe summary scope"}</small>
            </span>
          </label>
        ))}
      </div>
      {rawExportRequested && (
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={confirmRawExport}
            disabled={!debugEnabled}
            onChange={(event) => setConfirmRawExport(event.target.checked)}
          />
          I explicitly confirm raw debug export preview/create for selected local scopes.
        </label>
      )}
      <div className="button-row">
        <button type="button" disabled={!canPreview} onClick={() => onPreview(true, rawExportRequested ? confirmRawExport : true)}>
          Preview Debug Export
        </button>
        <button type="button" disabled={!canCreate} onClick={() => onCreate(true, rawExportRequested ? confirmRawExport : true)}>
          Create Local Debug Export
        </button>
      </div>
      <ErrorPanel message={error} compact />
      <div className="grid two-column">
        <div>
          <h4>Selected scopes</h4>
          <ItemList
            emptyText="No debug export scopes selected."
            items={selectedScopes.map((scopeId) => {
              const scope = SAFE_DEBUG_EXPORT_SCOPES.find((item) => item.id === scopeId);
              return <span key={scopeId}>{scope?.label ?? scopeId}: {scope?.rawRisk ? "raw gated" : "safe summary"}</span>;
            })}
          />
        </div>
        <div>
          <h4>Excluded from export</h4>
          <ItemList
            emptyText="No exclusions listed."
            items={["API key", "provider secrets", "raw env", "Authorization header", "raw prompt/output", "mature/private by default", "hidden text full content"].map((item) => (
              <RedactedValue key={item} value={item} />
            ))}
          />
        </div>
      </div>
      {diagnosticsPreview && (
        <details>
          <summary>Debug export preview safe manifest</summary>
          <SafeJSON value={{
            bundle_id: diagnosticsPreview.manifest.bundle_id,
            debug_bundle: diagnosticsPreview.manifest.debug_bundle,
            included_sections: selectedScopes,
            excluded_sections: diagnosticsPreview.manifest.excluded_sections,
            redaction_policy: diagnosticsPreview.manifest.redaction_policy,
            contains_secrets: diagnosticsPreview.manifest.contains_secrets,
            contains_hidden_debug_mature_private: diagnosticsPreview.manifest.contains_hidden_debug_mature_private
          }} />
        </details>
      )}
      {diagnosticsCreateResult && (
        <SuccessPanel compact message={`Local debug export created: ${diagnosticsCreateResult.bundle_path_summary ?? diagnosticsCreateResult.manifest.bundle_id}. No upload was performed.`} />
      )}
    </SectionCard>
  );
}

function LocalConfigWizardPanel({
  summary,
  startupChecks,
  error,
  onRefresh,
  onOpenProviders
}: {
  summary: LocalStudioConfigSummary | null;
  startupChecks: LocalStudioStartupChecks | null;
  error: string;
  onRefresh: () => void;
  onOpenProviders: () => void;
}) {
  return (
    <SectionCard title="Local Config Wizard" description="Review local configuration status without showing raw env, API keys, or database connection strings.">
      <div className="section-heading-row">
        <div>
          <h4>Config Status</h4>
          <p className="muted">This wizard cannot write .env and cannot store secrets.</p>
        </div>
        <div className="quick-actions">
          <button type="button" onClick={onRefresh}>Refresh Config</button>
          <button type="button" onClick={onOpenProviders}>Provider Setup Wizard</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Database" value={summary?.database_configured ? "configured" : "missing"} detail="DATABASE_URL value is not displayed." />
        <SafeSummaryCard title="Workspace root" value={summary?.project_root_configured ? "configured" : "missing"} detail="Only redacted safe path summaries are shown." />
        <SafeSummaryCard title="Log directory" value="local ignored" detail="Log paths stay local and are summarized, not exposed as sensitive full paths." />
        <SafeSummaryCard title="Backup directory" value="local ignored" detail="Backups are dry-run first and excluded from git/desktop bundles." />
        <SafeSummaryCard title="Privacy defaults" value="safe" detail="Secrets, raw env, hidden/debug, and mature/private content are excluded by default." />
        <SafeSummaryCard title="Provider profiles" value={String(summary?.provider_profiles_count ?? 0)} detail="Use api_key_env or secret_ref only." />
        <SafeSummaryCard title="Debug API" value={summary?.debug_enabled ? "enabled" : "disabled"} detail="Debug views require ENABLE_DEBUG_API." />
        <SafeSummaryCard title="Authoring API" value={summary?.authoring_enabled ? "enabled" : "disabled"} detail="Authoring actions still use backend validation." />
        <SafeSummaryCard title="Module API" value={summary?.module_api_enabled ? "enabled" : "disabled"} detail="Modules cannot execute arbitrary code." />
        <SafeSummaryCard title="Quality API" value={summary?.quality_api_enabled ? "available" : "unavailable"} detail="Quality reports are local safe summaries." />
      </div>
      {startupChecks?.warnings.length ? <p className="muted">{startupChecks.warnings.join(", ")}</p> : null}
    </SectionCard>
  );
}

function ProviderSetupWizardPanel() {
  const providerTypes = ["openai", "openai_compatible", "local_http", "relay", "mock/local_stub"];
  const allowedModes = ["Novel", "Tavern", "World", "Cross-Mode", "Quality"];
  return (
    <SectionCard title="Provider Setup Wizard" description="Guided local Provider setup. The frontend never asks for a plaintext API key; use api_key_env or secret_ref only.">
      <div className="mode-landing-grid">
        <FeatureCard title="Step 1: provider type" detail={providerTypes.join(", ")} />
        <FeatureCard title="Step 2: model and base URL" detail="Fill display_name, model_id, and base_url or base_url_env." />
        <FeatureCard title="Step 3: secret reference" detail="Use api_key_env or secret_ref. No plaintext api_key field is provided." />
        <FeatureCard title="Step 4: allowed modes" detail={allowedModes.join(", ")} />
        <FeatureCard title="Step 5: safe provider status" detail="Shows configured / missing env / model capability / routing warning only; key values stay hidden." />
        <FeatureCard title="Step 6: dry-run validation" detail="Validation is safe and does not call real providers by default." />
      </div>
      <SecretSafeNotice compact />
    </SectionCard>
  );
}

function BackupRestoreWizardPanel({
  plan,
  result,
  restorePlan,
  error,
  onDryRun,
  onCreate,
  onRestoreDryRun
}: {
  plan: BackupPlan | null;
  result: BackupCreateResponse | null;
  restorePlan: RestorePlan | null;
  error: string;
  onDryRun: () => void;
  onCreate: () => void;
  onRestoreDryRun: (backupPath: string, targetProjectId: string) => void;
}) {
  const [backupPath, setBackupPath] = useState<string>("backups/latest.zip");
  const [targetProjectId, setTargetProjectId] = useState<string>("restored_project");
  return (
    <SectionCard title="Backup / Restore Wizard" description="Local backup and restore are dry-run first. Secrets, .env, logs/cache/build outputs, debug-only data, and mature/private content are excluded by default.">
      <ErrorPanel message={error} compact />
      <div className="quick-actions">
        <button type="button" onClick={onDryRun}>Backup Dry-Run Preview</button>
        <button type="button" onClick={onCreate} disabled={!plan || plan.blockers.length > 0}>Explicit Confirm Create Backup</button>
      </div>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Backup policy" value="dry-run first" detail="Create is disabled until a backup dry-run preview exists and has no blockers." />
        <SafeSummaryCard title="Default exclusions" value="safe" detail=".env, API keys, provider secrets, databases, logs/cache, build outputs, debug-only data, and mature/private content." />
        <SafeSummaryCard title="Restore policy" value="dry-run first" detail="Restore apply requires zip/path/executable/secret blockers to be clear and explicit confirmation." />
      </div>
      {plan ? (
        <div className="safe-summary-grid">
          <SafeSummaryCard title="Plan" value={plan.plan_id} detail={plan.dry_run ? "dry-run only" : "apply"} />
          <SafeSummaryCard title="Would write" value={String(plan.would_write_files.length)} detail={plan.would_write_files.join(", ")} />
          <SafeSummaryCard title="Excluded" value={String(plan.excluded_items.length)} detail={plan.excluded_items.join(", ")} />
          <SafeSummaryCard title="Blockers" value={String(plan.blockers.length)} detail={plan.blockers.join(", ") || "none"} />
        </div>
      ) : (
        <EmptyState title="No backup dry-run yet." detail="Run dry-run before creating a local backup." />
      )}
      {result && <SuccessPanel message={`Backup created: ${result.backup_path_summary ?? result.manifest.manifest_id}`} compact />}
      <div className="template-grid">
        <label>
          Backup file for restore dry-run
          <input value={backupPath} onChange={(event) => setBackupPath(event.target.value)} />
        </label>
        <label>
          Target project id
          <input value={targetProjectId} onChange={(event) => setTargetProjectId(event.target.value)} />
        </label>
      </div>
      <button type="button" onClick={() => onRestoreDryRun(backupPath, targetProjectId)}>Restore Dry-Run Preview</button>
      {restorePlan && (
        <div className="safe-summary-grid">
          <SafeSummaryCard title="Restore valid" value={restorePlan.backup_valid ? "yes" : "no"} detail={restorePlan.target_project_id} />
          <SafeSummaryCard title="Conflicts" value={String(restorePlan.conflicts.length)} detail={restorePlan.conflicts.join(", ") || "none"} />
          <SafeSummaryCard title="Blockers" value={String(restorePlan.blockers.length)} detail={restorePlan.blockers.join(", ") || "none"} />
          <SafeSummaryCard title="Confirm restore" value="manual required" detail="This UI only previews restore safety; overwrite/apply remains confirm-gated." />
        </div>
      )}
    </SectionCard>
  );
}

function ErrorRecoveryWizardPanel({
  issues,
  plan,
  error,
  onRefresh,
  onDryRun
}: {
  issues: RecoveryIssue[];
  plan: RecoveryPlan | null;
  error: string;
  onRefresh: () => void;
  onDryRun: () => void;
}) {
  return (
    <SectionCard title="Error Recovery Wizard" description="Local recovery suggestions are dry-run first. Destructive recovery is blocked/manual-only.">
      <div className="quick-actions">
        <button type="button" onClick={onRefresh}>Refresh Issues</button>
        <button type="button" onClick={onDryRun}>Dry-Run Recovery</button>
      </div>
      <ErrorPanel message={error} compact />
      {issues.length ? (
        <div className="desktop-health-list">
          {issues.map((issue) => (
            <article className={`desktop-health-item ${issue.severity}`} key={issue.issue_id}>
              <div className="section-heading-row">
                <strong>{issue.category}: {issue.issue_id}</strong>
                <span className={`status-pill ${issue.severity}`}>{issue.disposition}</span>
              </div>
              <p>{issue.safe_summary}</p>
              <p className="muted">{issue.suggested_action}</p>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No recovery issues." detail="Refresh to detect local recovery suggestions." />
      )}
      {plan && <p className="muted">Plan {plan.plan_id}: {plan.actions.length} suggested action(s), {plan.blockers.length} blocker(s).</p>}
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Restart backend/frontend" value="manual safe action" detail="Use the local launcher scripts; recovery UI does not run destructive shell commands." />
        <SafeSummaryCard title="Reload project summary" value="safe" detail="Refreshes local safe summaries without reading arbitrary files." />
        <SafeSummaryCard title="Restore from backup" value="dry-run required" detail="Use Backup / Restore Wizard before any confirmed restore." />
        <SafeSummaryCard title="Open diagnostics preview" value="local-only" detail="Diagnostics preview is redacted and does not write or upload by default." />
      </div>
    </SectionCard>
  );
}

function LocalLogViewerPanel({
  logs,
  error,
  debugEnabled,
  onRefresh
}: {
  logs: LocalLogListResponse | null;
  error: string;
  debugEnabled: boolean;
  onRefresh: () => void;
}) {
  const [levelFilter, setLevelFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const entries = logs?.logs ?? [];
  const levels = Array.from(new Set(entries.map((entry) => entry.level))).sort();
  const categories = Array.from(new Set(entries.map((entry) => entry.category))).sort();
  const filteredEntries = entries.filter((entry) => (
    (levelFilter === "all" || entry.level === levelFilter) &&
    (categoryFilter === "all" || entry.category === categoryFilter)
  ));
  const redactedCount = entries.filter((entry) => entry.redacted).length;
  return (
    <SectionCard title="Local Log Viewer" description="Shows redacted local log summaries from the allowed logs directory only. API keys, Authorization headers, raw env, DB URLs, hidden facts, mature/private content, and raw state_deltas are redacted.">
      <div className="section-heading-row">
        <div>
          <h4>Safe Logs</h4>
          <p className="muted">Debug logs are gated by ENABLE_DEBUG_API: {debugEnabled ? "enabled" : "disabled"}.</p>
        </div>
        <button type="button" onClick={onRefresh}>Refresh Logs</button>
      </div>
      <ErrorPanel message={error} compact />
      {logs?.warnings.length ? <p className="muted">{logs.warnings.join(", ")}</p> : null}
      <div className="template-grid">
        <label>
          Level filter
          <select value={levelFilter} onChange={(event) => setLevelFilter(event.target.value)}>
            <option value="all">all</option>
            {levels.map((level) => <option key={level} value={level}>{level}</option>)}
          </select>
        </label>
        <label>
          Component filter
          <select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}>
            <option value="all">all</option>
            {categories.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
        </label>
        <SafeSummaryCard title="Redacted entries" value={String(redactedCount)} detail="Copy safe summary only; raw log lines and secrets are not exposed." />
      </div>
      {filteredEntries.length ? (
        <ul className="compact-list">
          {filteredEntries.slice(0, 20).map((entry, index) => (
            <li key={`${entry.source}-${index}`}>
              <strong>{entry.level}</strong> {entry.category} / {entry.source}: {entry.message}
              {entry.redacted && <span className="badge">redacted</span>}
            </li>
          ))}
        </ul>
      ) : (
        <EmptyState title="No local logs." detail="Launcher logs live under ignored logs/ and are redacted before display." />
      )}
    </SectionCard>
  );
}

function QualityDashboardUXPanel({
  worldHealth,
  narrativeEvalReports,
  playtestReports,
  scenarioRegressionRuns,
  contentCoverage
}: {
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  playtestReports: PlaytestReport[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  contentCoverage: ContentCoverageReport | null;
}) {
  const blockerCount = (worldHealth?.blockers?.length ?? 0) + narrativeEvalReports.reduce((count, report) => count + report.failed, 0);
  const warningCount = (worldHealth?.warnings?.length ?? 0) + (contentCoverage ? Object.values(contentCoverage.hidden_entities_redacted).reduce((total, value) => total + value, 0) : 0);
  const categories = ["Project", "World", "Novel", "Tavern", "Cross-Mode", "Provider", "Mods", "Modules", "RP/Mature"];
  return (
    <SectionCard title="Quality Gate Dashboard" description="Safe overview of blockers, warnings, and next local actions.">
      <div className="section-heading-row">
        <div>
          <h4>One-Click Quality Gate</h4>
          <p className="muted">Scope choices: project, world, novel, tavern, cross-mode, providers, mods, modules, rp/mature, all. Reports are safe summaries only.</p>
        </div>
        <button type="button" disabled title="Connects to local quality APIs; disabled here until a project/world scope is selected.">Run One-Click Quality Gate</button>
      </div>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Overall status" value={blockerCount ? "blocked" : worldHealth ? "review" : "not run"} detail="Run the relevant local quality gates before release." />
        <SafeSummaryCard title="Blockers" value={String(blockerCount)} detail="Safe summaries only; hidden facts are not printed." />
        <SafeSummaryCard title="Warnings" value={String(warningCount)} detail="Warnings guide the next manual review." />
        <SafeSummaryCard title="Playtests" value={String(playtestReports.length)} detail="Existing reports remain local." />
        <SafeSummaryCard title="Scenario runs" value={String(scenarioRegressionRuns.length)} detail="Regression results are local-only." />
        <SafeSummaryCard title="Last run summary" value={worldHealth ? "available" : "not run"} detail="Shows local blocker/warning counts and safe suggestions, never hidden text." />
      </div>
      <div className="mode-landing-grid">
        {categories.map((category) => (
          <FeatureCard
            key={category}
            title={category}
            detail="Open the dedicated panel for full safe issue details and suggested actions."
            status={<ValidationStatusBadge status={blockerCount ? "warning" : "not_run"} />}
          />
        ))}
      </div>
    </SectionCard>
  );
}

const QUALITY_GATE_CATEGORIES = [
  "Project",
  "World",
  "Novel",
  "Tavern",
  "Cross-Mode",
  "Provider",
  "Mods",
  "Modules",
  "RP/Mature",
  "Backup/Diagnostics"
] as const;

type UnifiedQualityGateCategory = (typeof QUALITY_GATE_CATEGORIES)[number];
type UnifiedQualityGateRow = {
  category: UnifiedQualityGateCategory;
  blockers: number;
  errors: number;
  warnings: number;
  lastRunTime: string;
  suggestedNextActions: string[];
  run?: () => void;
};

function UnifiedQualityGateDashboard({
  worldHealth,
  narrativeEvalReports,
  playtestReports,
  scenarioRegressionRuns,
  contentCoverage,
  diagnosticsBundlePreview,
  backupPlan,
  configSummary,
  localConfigIssues,
  onRunWorld,
  onRunNovel,
  onRunPlaytest,
  onRunDiagnostics
}: {
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  playtestReports: PlaytestReport[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  contentCoverage: ContentCoverageReport | null;
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  backupPlan: BackupPlan | null;
  configSummary: StudioConfigSummary | null;
  localConfigIssues: LocalConfigIssue[];
  onRunWorld: () => void;
  onRunNovel: () => void;
  onRunPlaytest: () => void;
  onRunDiagnostics: () => void;
}) {
  const [selectedCategory, setSelectedCategory] = useState<UnifiedQualityGateCategory>("Project");
  const rows = useMemo(
    () =>
      buildUnifiedQualityGateRows({
        worldHealth,
        narrativeEvalReports,
        playtestReports,
        scenarioRegressionRuns,
        contentCoverage,
        diagnosticsBundlePreview,
        backupPlan,
        configSummary,
        localConfigIssues,
        onRunWorld,
        onRunNovel,
        onRunPlaytest,
        onRunDiagnostics
      }),
    [backupPlan, configSummary, contentCoverage, diagnosticsBundlePreview, localConfigIssues, narrativeEvalReports, onRunDiagnostics, onRunNovel, onRunPlaytest, onRunWorld, playtestReports, scenarioRegressionRuns, worldHealth]
  );
  const blockerCount = rows.reduce((total, row) => total + row.blockers, 0);
  const errorCount = rows.reduce((total, row) => total + row.errors, 0);
  const warningCount = rows.reduce((total, row) => total + row.warnings, 0);
  const overall = blockerCount || errorCount ? "fail" : warningCount ? "review" : rows.some((row) => row.lastRunTime !== "not run") ? "pass" : "not run";
  const selectedRow = rows.find((row) => row.category === selectedCategory) ?? rows[0];

  function runAllAvailable() {
    rows.forEach((row) => row.run?.());
  }

  return (
    <section className="studio-section unified-quality-gate">
      <div className="authoring-pane-header">
        <div>
          <h3>Quality Gate Unified Dashboard Pro</h3>
          <p className="muted">Unified local quality status for Project, World, Novel, Tavern, Cross-Mode, Provider, Mods, Modules, RP/Mature, Backup, and Diagnostics.</p>
        </div>
        <ValidationStatusBadge status={overall === "fail" ? "failed" : overall === "pass" ? "passed" : overall === "review" ? "warning" : "not_run"} />
      </div>
      <FilterToolbar>
        <button type="button" onClick={runAllAvailable} disabled={!rows.some((row) => row.run)}>
          Run All Available Gates
        </button>
        <label>
          Selected gate
          <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value as UnifiedQualityGateCategory)}>
            {rows.map((row) => (
              <option key={row.category} value={row.category}>{row.category}</option>
            ))}
          </select>
        </label>
        <button type="button" onClick={() => selectedRow.run?.()} disabled={!selectedRow.run}>
          Run Selected Gate
        </button>
      </FilterToolbar>
      <div className="timeline-summary">
        <span>overall: {overall}</span>
        <span>{blockerCount} blockers</span>
        <span>{errorCount} errors</span>
        <span>{warningCount} warnings</span>
      </div>
      <div className="mode-landing-grid">
        {rows.map((row) => (
          <section className="feature-card" key={row.category}>
            <div>
              <h4>{row.category}</h4>
              <p className="muted">Last run: {row.lastRunTime}</p>
            </div>
            <dl className="event-details">
              <dt>Blockers</dt><dd>{row.blockers}</dd>
              <dt>Errors</dt><dd>{row.errors}</dd>
              <dt>Warnings</dt><dd>{row.warnings}</dd>
            </dl>
            <ItemList emptyText="No suggested action." items={row.suggestedNextActions.slice(0, 3).map((action) => <span key={action}>{redactLeakSummary(action)}</span>)} />
          </section>
        ))}
      </div>
    </section>
  );
}

function buildUnifiedQualityGateRows({
  worldHealth,
  narrativeEvalReports,
  playtestReports,
  scenarioRegressionRuns,
  contentCoverage,
  diagnosticsBundlePreview,
  backupPlan,
  configSummary,
  localConfigIssues,
  onRunWorld,
  onRunNovel,
  onRunPlaytest,
  onRunDiagnostics
}: {
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  playtestReports: PlaytestReport[];
  scenarioRegressionRuns: ScenarioRegressionRun[];
  contentCoverage: ContentCoverageReport | null;
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  backupPlan: BackupPlan | null;
  configSummary: StudioConfigSummary | null;
  localConfigIssues: LocalConfigIssue[];
  onRunWorld: () => void;
  onRunNovel: () => void;
  onRunPlaytest: () => void;
  onRunDiagnostics: () => void;
}): UnifiedQualityGateRow[] {
  const latestNarrative = narrativeEvalReports.at(-1) ?? null;
  const latestPlaytest = playtestReports.at(-1) ?? null;
  const latestScenario = scenarioRegressionRuns.at(-1) ?? null;
  const playtestIssues = latestPlaytest ? latestPlaytest.errors.length + latestPlaytest.invariant_violations.length + latestPlaytest.visibility_leaks.length + latestPlaytest.save_load_failures.length : 0;
  const scenarioFailures = latestScenario?.case_results.filter((result) => !result.passed).length ?? 0;
  const providerWarnings = configSummary?.api_key_configured ? 0 : 1;
  const diagnosticsWarnings = (diagnosticsBundlePreview?.warnings.length ?? 0) + (backupPlan?.warnings.length ?? 0);
  const diagnosticsBlockers = Number(Boolean(diagnosticsBundlePreview?.manifest.contains_secrets || diagnosticsBundlePreview?.manifest.contains_hidden_debug_mature_private));
  const coverageWarnings = contentCoverage ? Object.values(contentCoverage.hidden_entities_redacted).reduce((total, value) => total + value, 0) : 0;
  return [
    qualityRow("Project", localConfigIssues.filter((issue) => issue.severity === "error").length, 0, localConfigIssues.filter((issue) => issue.severity !== "error").length, "current", localConfigIssues.length ? localConfigIssues.map((issue) => issue.message) : ["Project config has no loaded blockers."], undefined),
    qualityRow("World", worldHealth?.blockers.length ?? 0, 0, (worldHealth?.warnings.length ?? 0) + coverageWarnings, worldHealth?.created_at ?? "not run", worldHealth?.recommended_actions ?? ["Run World Health Gate."], onRunWorld),
    qualityRow("Novel", 0, latestNarrative?.failed ?? 0, 0, latestNarrative?.created_at ?? "not run", latestNarrative ? ["Review failed Novel quality cases."] : ["Run Novel quality eval."], onRunNovel),
    qualityRow("Tavern", 0, 0, 0, "safe summary only", ["Run RP Safety Dashboard from Tavern Studio for detailed checks."], undefined),
    qualityRow("Cross-Mode", scenarioFailures, 0, latestScenario ? 0 : 1, latestScenario?.created_at ?? "not run", latestScenario ? ["Review failed scenario regression cases."] : ["Run scenario regression for cross-mode paths."], undefined),
    qualityRow("Provider", 0, 0, providerWarnings, "current", providerWarnings ? ["Configure Provider profile by api_key_env or secret_ref."] : ["Provider configuration summary loaded."], undefined),
    qualityRow("Mods", 0, 0, 1, "safe summary only", ["Run Mod Quality Gate from Authoring / Mod Studio."], undefined),
    qualityRow("Modules", 0, playtestIssues, 0, latestPlaytest?.created_at ?? "not run", latestPlaytest ? ["Review module playtest failures and hidden leak warnings."] : ["Run module playtests."], onRunPlaytest),
    qualityRow("RP/Mature", 0, 0, 1, "safe summary only", ["Confirm Mature module remains default-off and run RP/Mature quality gates when configured."], undefined),
    qualityRow("Backup/Diagnostics", diagnosticsBlockers, 0, diagnosticsWarnings, diagnosticsBundlePreview?.manifest.created_at ?? "not run", diagnosticsWarnings || diagnosticsBlockers ? ["Review backup/diagnostics exclusions and redaction warnings."] : ["Preview diagnostics bundle and backup plan before release."], onRunDiagnostics),
  ];
}

function qualityRow(
  category: UnifiedQualityGateCategory,
  blockers: number,
  errors: number,
  warnings: number,
  lastRunTime: string,
  suggestedNextActions: string[],
  run: (() => void) | undefined
): UnifiedQualityGateRow {
  return { category, blockers, errors, warnings, lastRunTime, suggestedNextActions: suggestedNextActions.map(redactReportText), run };
}

function WorldStudioLanding({
  visibleState,
  sessionId,
  selectedSaveId,
  saves,
  debugEnabled
}: {
  visibleState: VisibleState | null;
  sessionId: string;
  selectedSaveId: string;
  saves: SaveSummary[];
  debugEnabled: boolean;
}) {
  return (
    <section className="world-landing">
      <PageHeader
        eyebrow="World Studio"
        title="Local World Entry"
        description="Normal view uses visible state only. World changes still go through backend rules, StateDelta, and EventLog."
      />
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Active session" value={sessionId ? "Started" : "No active session"} detail={selectedSaveId ? `Loaded save ${selectedSaveId}` : "Start or load a local save."} />
        <SafeSummaryCard title="Visible location" value={visibleState?.location.name ?? "Unknown"} detail="Hidden locations and NPC secrets are excluded." />
        <SafeSummaryCard title="Visible NPCs" value={String(visibleState?.visible_npcs.length ?? 0)} detail="Only player-visible NPC summaries are shown." />
        <SafeSummaryCard title="Quests" value={String(visibleState?.quests.length ?? 0)} detail="Normal view excludes hidden quest facts." />
        <SafeSummaryCard title="Inventory" value={String(visibleState?.inventory.length ?? 0)} detail="Visible inventory summary only." />
        <SafeSummaryCard title="Advanced modules" value="Status safe" detail="Combat/economy/faction module details stay backend-authoritative." />
        <SafeSummaryCard title="Timeline replay" value={debugEnabled ? "Debug enabled" : "Debug gated"} detail="Raw debug data requires ENABLE_DEBUG_API." />
        <SafeSummaryCard title="Saves" value={String(saves.length)} detail="Save/load remains local." />
      </div>
    </section>
  );
}

function ScriptModEntryPanel({
  modules,
  moduleDetail,
  compatibilityMatrix,
  moduleQualityGate,
  auditRecords
}: {
  modules: ModuleBrowserSummary[];
  moduleDetail: ModuleBrowserDetail | null;
  compatibilityMatrix: ModCompatibilityMatrix | null;
  moduleQualityGate: ModQualityGateResult | null;
  auditRecords: ModAuditRecord[];
}) {
  const byType = modules.reduce<Record<string, number>>((counts, item) => {
    counts[item.package_type] = (counts[item.package_type] ?? 0) + 1;
    return counts;
  }, {});
  const unsafeCount = modules.filter((item) => item.permission_risk_level === "blocked" || item.permission_risk_level === "high").length;
  const packageTypes = [
    "Script Pack",
    "World Extension",
    "Character Pack",
    "Prompt Pack",
    "Provider Pack",
    "Narrative Style Mod",
    "RP Profile Mod",
    "Action Mod",
    "Rule Module"
  ];
  return (
    <section className="module-entry-panel">
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Local packages" value={String(modules.length)} detail="Scanned local manifests only; packages are not executed." />
        <SafeSummaryCard title="Unsafe packages" value={String(unsafeCount)} detail="Blocked or high-risk packages require review." />
        <SafeSummaryCard title="Compatibility warnings" value={String((compatibilityMatrix?.entries ?? []).reduce((count, entry) => count + entry.warnings.length, 0) + (compatibilityMatrix?.conflicts_summary.length ?? 0))} detail="Matrix warnings stay local." />
        <SafeSummaryCard title="Certification" value={moduleDetail?.summary.validation_status ?? "not loaded"} detail="Certification status is a safe summary." />
        <SafeSummaryCard title="Quality Gate" value={moduleQualityGate ? (moduleQualityGate.ok ? "passed" : "blocked") : "not run"} detail="Run before import/apply." />
        <SafeSummaryCard title="Recent imports/exports" value={String(auditRecords.length)} detail="Audit trail summaries redact secrets." />
      </div>
      <div className="mode-landing-grid">
        {packageTypes.map((type) => (
          <FeatureCard
            key={type}
            title={type}
            detail={`${byType[type.toLowerCase().replaceAll(" ", "_")] ?? 0} local packages found`}
            status={<RiskBadge level="unknown" />}
          />
        ))}
      </div>
      <SecretSafeNotice compact />
      <p className="muted">No online marketplace, no remote auto-download, and no arbitrary code execution.</p>
    </section>
  );
}

function AuthoringWorkspaceShell({
  title,
  status,
  children,
  sidebar,
  footer
}: {
  title: string;
  status: string;
  children: ReactNode;
  sidebar?: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="authoring-workspace-shell">
      <div className="authoring-shell-header">
        <div>
          <h3>{title}</h3>
          <p className="muted">Local authoring workspace. Drafts and package candidates require validation, dry-run, and explicit confirm before local apply.</p>
        </div>
        <LocalOnlyBadge />
      </div>
      <div className="authoring-shell-grid">
        <div className="authoring-shell-main">{children}</div>
        <aside className="authoring-shell-sidebar">
          {sidebar ?? <EmptyState title="No authoring sidebar." detail="Validation, preview, permissions, and quality summaries appear here." />}
        </aside>
      </div>
      <div className="local-status-bar">
        <span>{status}</span>
        <span>No online marketplace</span>
        <span>No remote download</span>
        <span>No arbitrary code execution</span>
      </div>
      {footer}
    </section>
  );
}

function AuthoringStudioProDashboard({
  activeTool,
  selectedWorldId,
  selectedFile,
  isDirty,
  validation,
  preview,
  onOpenTool
}: {
  activeTool: AuthoringToolId;
  selectedWorldId: string;
  selectedFile: string;
  isDirty: boolean;
  validation: AuthoringValidation | null;
  preview: AuthoringFilePreviewResponse | null;
  onOpenTool: (toolId: AuthoringToolId) => void;
}) {
  const editorGroups = [
    { title: "World Pack Editor Pro", detail: "metadata, locations, NPCs, items, quests, facts, factions, rumors, relationships", tool: "world_pack_wizard" as AuthoringToolId },
    { title: "Script Pack Editor Pro", detail: "scenarios, quest drafts, novel/tavern templates, cross-mode templates, quality checks", tool: "template_wizard" as AuthoringToolId },
    { title: "Character Pack Editor Pro", detail: "CharacterProfile, TavernCharacter, RPProfile, VoiceProfile, cards, World NPC drafts", tool: "rp_characters" as AuthoringToolId },
    { title: "Quest Graph Editor Pro", detail: "nodes, objectives, triggers, conditions, rewards, failures, player-visible preview", tool: "quests" as AuthoringToolId },
    { title: "Location / Map Authoring Pro", detail: "locations, exits, regions, hidden/discovery conditions, map preview", tool: "map" as AuthoringToolId },
    { title: "NPC / Faction / Relationship Authoring Pro", detail: "public NPC fields, faction refs, secrets authoring-only, safe relationship preview", tool: "social" as AuthoringToolId },
    { title: "Item / Economy / Trade Authoring Pro", detail: "items, prices, merchants, markets, trade routes, crafting recipes", tool: "economy" as AuthoringToolId },
    { title: "Rumor / Crime / Consequence Authoring Pro", detail: "rumor spread, witness conditions, faction reactions, quest flags, event tags", tool: "rumor_crime" as AuthoringToolId },
    { title: "Advanced Module Authoring Panels", detail: "tactical, economy, faction, magic, hacking, crafting, deduction, survival, cultivation", tool: "advanced_modules" as AuthoringToolId },
    { title: "Action Mod Editor / Test Harness", detail: "structured DSL form, StateDelta proposal preview, local safe test report", tool: "action_mods" as AuthoringToolId }
  ];
  const blockers = validation?.errors.length ?? 0;
  const warnings = validation?.warnings.length ?? 0;
  return (
    <section className="module-pro-panel">
      <div className="authoring-shell-header">
        <div>
          <h3>Authoring / Mod Workspace Pro</h3>
          <p className="muted">Field-level local editors route through preview, validation, dry-run, and explicit save/apply. Authoring does not modify active GameState.</p>
        </div>
        <div className="button-row">
          <span className="badge">{selectedWorldId || "no world"}</span>
          <span className="badge">{selectedFile}</span>
          <span className={`badge ${isDirty ? "warning" : "ok"}`}>{isDirty ? "dirty" : "clean"}</span>
        </div>
      </div>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Validation state" value={validation?.ok ? "pass" : blockers ? "blocked" : "not clear"} detail={`${blockers} blockers · ${warnings} warnings`} />
        <SafeSummaryCard title="Preview state" value={preview ? "ready" : "not run"} detail="Preview is safe summary only; hidden facts stay authoring-only." />
        <SafeSummaryCard title="Safe apply" value="confirm required" detail="Apply writes local content pack/project files only after validation and dry-run." />
      </div>
      <div className="module-filter-grid">
        {editorGroups.map((group) => (
          <button
            type="button"
            key={group.title}
            className={`module-browser-row ${activeTool === group.tool ? "selected-list-button" : ""}`}
            onClick={() => onOpenTool(group.tool)}
          >
            <strong>{group.title}</strong>
            <span>{group.detail}</span>
            <small>Open editor</small>
          </button>
        ))}
      </div>
    </section>
  );
}

function ModuleBrowserProPanel({
  modules,
  selectedModuleId,
  moduleSearchQuery,
  moduleTypeFilter,
  moduleRiskFilter,
  moduleValidationFilter,
  moduleCertificationFilter,
  moduleCertificationLevel,
  moduleQualityGate,
  onSearchChange,
  onTypeFilterChange,
  onRiskFilterChange,
  onValidationFilterChange,
  onCertificationFilterChange,
  onSelectModule
}: {
  modules: ModuleBrowserSummary[];
  selectedModuleId: string;
  moduleSearchQuery: string;
  moduleTypeFilter: string;
  moduleRiskFilter: string;
  moduleValidationFilter: string;
  moduleCertificationFilter: string;
  moduleCertificationLevel: string;
  moduleQualityGate: ModQualityGateResult | null;
  onSearchChange: (value: string) => void;
  onTypeFilterChange: (value: string) => void;
  onRiskFilterChange: (value: string) => void;
  onValidationFilterChange: (value: string) => void;
  onCertificationFilterChange: (value: string) => void;
  onSelectModule: (packageId: string) => void;
}) {
  const packageTypes = Array.from(new Set(modules.map((module) => module.package_type))).sort();
  const validationStatuses = Array.from(new Set(modules.map((module) => module.validation_status))).sort();
  const query = moduleSearchQuery.trim().toLowerCase();
  const filtered = modules.filter((module) => {
    const selectedCertification = module.package_id === selectedModuleId ? moduleCertificationLevel || moduleQualityGate?.certification_level || "not_run" : "not_run";
    return (
      (!query || `${module.package_id} ${module.name}`.toLowerCase().includes(query)) &&
      (moduleTypeFilter === "all" || module.package_type === moduleTypeFilter) &&
      (moduleRiskFilter === "all" || module.permission_risk_level === moduleRiskFilter) &&
      (moduleValidationFilter === "all" || module.validation_status === moduleValidationFilter) &&
      (moduleCertificationFilter === "all" || selectedCertification === moduleCertificationFilter)
    );
  });
  return (
    <section className="module-pro-panel">
      <div className="section-heading-row">
        <div>
          <h4>Module Browser Pro</h4>
          <p className="muted">Package list is local-only metadata. No online marketplace, no remote download, no package execution.</p>
        </div>
        <LocalOnlyBadge />
      </div>
      <div className="module-filter-grid">
        <label>
          Search package
          <input value={moduleSearchQuery} onChange={(event) => onSearchChange(event.target.value)} placeholder="package id or name" />
        </label>
        <label>
          Package type
          <select value={moduleTypeFilter} onChange={(event) => onTypeFilterChange(event.target.value)}>
            <option value="all">All</option>
            {packageTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <label>
          Risk level
          <select value={moduleRiskFilter} onChange={(event) => onRiskFilterChange(event.target.value)}>
            <option value="all">All</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="blocked">Blocked</option>
          </select>
        </label>
        <label>
          Validation
          <select value={moduleValidationFilter} onChange={(event) => onValidationFilterChange(event.target.value)}>
            <option value="all">All</option>
            {validationStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
        </label>
        <label>
          Certification
          <select value={moduleCertificationFilter} onChange={(event) => onCertificationFilterChange(event.target.value)}>
            <option value="all">All</option>
            <option value="not_run">Not run</option>
            {CERTIFICATION_LEVELS.map((level) => <option key={level} value={level}>{level}</option>)}
          </select>
        </label>
      </div>
      <div className="module-browser-table">
        {filtered.length === 0 ? (
          <EmptyState title="No local modules match the filters." detail="Scan local modules or adjust filters. This UI never downloads remote packages." />
        ) : filtered.map((module) => {
          const selectedCertification = module.package_id === selectedModuleId ? moduleCertificationLevel || moduleQualityGate?.certification_level || "not_run" : "not_run";
          return (
            <button
              key={module.package_id}
              type="button"
              className={`module-browser-row ${module.package_id === selectedModuleId ? "selected-list-button" : ""}`}
              onClick={() => onSelectModule(module.package_id)}
            >
              <span><strong>{module.name}</strong><small>{module.package_id}</small></span>
              <span>{module.package_type}<small>v{module.version}</small></span>
              <ValidationStatusBadge status={moduleValidationBadgeStatus(module.validation_status)} />
              <RiskBadge level={moduleRiskBadgeLevel(module.permission_risk_level)} />
              <span>{module.compatibility_status}</span>
              <span>{selectedCertification}</span>
              <span>{module.local_only ? "local-only" : "review"}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function ModPermissionDashboardProPanel({
  modulePermissions,
  permissionSummaries,
  riskFilter,
  onRiskFilterChange
}: {
  modulePermissions: ModulePermissionSummary | null;
  permissionSummaries: ModulePermissionSummary[];
  riskFilter: string;
  onRiskFilterChange: (value: string) => void;
}) {
  const requested = new Set(moduleRequestedPermissions(modulePermissions));
  const dangerousRequested = new Set(modulePermissions?.dangerous_permissions ?? []);
  const safePermissions = moduleSafePermissions(modulePermissions);
  const affectedPackages = permissionSummaries.filter((summary) => riskFilter === "all" || summary.risk_level === riskFilter);
  return (
    <section className="module-pro-panel">
      <div className="section-heading-row">
        <div>
          <h4>Mod Permission Dashboard Pro</h4>
          <p className="muted">Dangerous permissions are default-deny. There is no UI to enable arbitrary code, network, filesystem, secrets, direct GameState writes, visibility bypass, or LLM calls.</p>
        </div>
        <RiskBadge level={moduleRiskBadgeLevel(modulePermissions?.risk_level ?? "unknown")} />
      </div>
      <label>
        Affected package risk filter
        <select value={riskFilter} onChange={(event) => onRiskFilterChange(event.target.value)}>
          <option value="all">All</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="blocked">Blocked</option>
        </select>
      </label>
      {modulePermissions ? (
        <div className="permission-matrix">
          {DANGEROUS_MODULE_PERMISSIONS.map((permission) => {
            const isRequested = requested.has(permission) || dangerousRequested.has(permission);
            return (
              <div key={permission} className="permission-row">
                <strong>{permission}</strong>
                <RiskBadge level="blocked" />
                <span>{isRequested ? "requested / blocked" : "blocked by default"}</span>
                <small>{modulePermissionReason(permission, isRequested, true)}</small>
              </div>
            );
          })}
          {safePermissions.map((permission) => (
            <div key={permission} className="permission-row">
              <strong>{permission}</strong>
              <RiskBadge level="safe" />
              <span>allowed</span>
              <small>{modulePermissionReason(permission, true, false)}</small>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No selected permission summary." detail="Select a local package to review permission details." />
      )}
      <details>
        <summary>Package affected list</summary>
        <ItemList
          emptyText="No packages match this risk filter."
          items={affectedPackages.map((summary) => (
            <span key={summary.package_id}>{summary.package_id}: {summary.risk_level} · {summary.dangerous_permissions.join(", ") || "safe declarative permissions"}</span>
          ))}
        />
      </details>
    </section>
  );
}

function CompatibilityMatrixProPanel({ matrix, selectedCompatibility }: { matrix: ModCompatibilityMatrix | null; selectedCompatibility: Record<string, unknown> | null }) {
  return (
    <section className="module-pro-panel">
      <div className="section-heading-row">
        <div>
          <h4>Compatibility Matrix UI Pro</h4>
          <p className="muted">Checks local package metadata only. It does not execute, enable, disable, or auto-resolve packages.</p>
        </div>
        <ValidationStatusBadge status={matrix?.ok ? "passed" : matrix ? "failed" : "not_run"} />
      </div>
      {matrix ? (
        <div className="stack">
          <div className="safe-summary-grid">
            <SafeSummaryCard title="Selected package set" value={String(matrix.entries.length)} detail="Current matrix selection is local." />
            <SafeSummaryCard title="Load order draft" value={String(matrix.load_order.length)} detail={matrix.load_order.join(" -> ") || "none"} />
            <SafeSummaryCard title="Conflicts" value={String(matrix.conflicts_summary.length)} detail={matrix.conflicts_summary.join(", ") || "none"} />
          </div>
          <div className="module-browser-table">
            {matrix.entries.map((entry) => (
              <div key={entry.package_id} className="module-browser-row static">
                <span><strong>{entry.package_id}</strong><small>order {entry.load_order_index ?? "n/a"}</small></span>
                <ValidationStatusBadge status={entry.compatible ? "passed" : "failed"} />
                <span>{entry.status}</span>
                <span>engine/schema safe summary</span>
                <span>permissions checked</span>
                <span>action/state namespace not executed</span>
                <span>{entry.errors.length ? `${entry.errors.length} blocker(s)` : "no blockers"}</span>
              </div>
            ))}
          </div>
          <ItemList emptyText="No matrix warnings." items={matrix.entries.flatMap((entry) => entry.warnings.map((warning) => <span key={`${entry.package_id}-${warning}`}>{entry.package_id}: {warning}</span>))} />
          <ItemList emptyText="No matrix blockers." items={matrix.entries.flatMap((entry) => entry.errors.map((error) => <span key={`${entry.package_id}-${error}`} className="danger-text">{entry.package_id}: {error}</span>))} />
        </div>
      ) : (
        <EmptyState title="No compatibility matrix." detail="Build the local module matrix after scanning packages." />
      )}
      {selectedCompatibility && (
        <p className="muted">Selected compatibility: {String(selectedCompatibility.status ?? "unknown")}; missing dependencies {stringListFromUnknown(selectedCompatibility.missing_dependencies).join(", ") || "none"}.</p>
      )}
    </section>
  );
}

function ExtensionCertificationProPanel({ moduleCertificationLevel, moduleQualityGate }: { moduleCertificationLevel: string; moduleQualityGate: ModQualityGateResult | null }) {
  return (
    <section className="module-pro-panel">
      <h4>Extension Certification UI Pro</h4>
      <p className="muted">Certification is local advisory only. It is not online certification, upload, package execution, or an absolute safety guarantee.</p>
      <div className="mode-landing-grid">
        {CERTIFICATION_LEVELS.map((level) => (
          <FeatureCard
            key={level}
            title={level}
            detail={level === "unsafe_blocked" ? "Blocked packages require manifest, permission, executable, secret, compatibility, and quality review." : "Local advisory level based on manifest and quality summaries."}
            status={<ValidationStatusBadge status={(moduleCertificationLevel || moduleQualityGate?.certification_level) === level ? (level === "unsafe_blocked" ? "failed" : "passed") : "not_run"} />}
          />
        ))}
      </div>
      {moduleQualityGate && (
        <ItemList
          emptyText="No certification blockers."
          items={[...moduleQualityGate.blockers, ...moduleQualityGate.warnings].map((item) => <span key={item}>{redactReportText(item)}</span>)}
        />
      )}
    </section>
  );
}

function ModQualityGateProPanel({ gate }: { gate: ModQualityGateResult | null }) {
  const categories = ["manifest", "permissions", "compatibility", "secrets", "executable files", "action tests", "hidden leaks", "migration impact"];
  return (
    <section className="module-pro-panel">
      <h4>Mod Quality Gate UI Pro</h4>
      <p className="muted">Local quality reports do not upload, execute packages, call LLMs, auto-fix, or expose hidden text/secrets.</p>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Overall" value={gate ? (gate.ok ? "passed" : "blocked") : "not run"} detail={gate?.package_id ?? "Select a package and run gate."} />
        <SafeSummaryCard title="Blockers" value={String(gate?.blockers.length ?? 0)} detail="Safe summaries only." />
        <SafeSummaryCard title="Warnings" value={String(gate?.warnings.length ?? 0)} detail="Review before export/apply." />
        <SafeSummaryCard title="Compatibility" value={gate?.compatibility_status ?? "not run"} detail="Matrix remains local." />
      </div>
      <div className="mode-landing-grid">
        {categories.map((category) => (
          <FeatureCard key={category} title={category} detail="Review safe blockers/warnings for this category." status={<ValidationStatusBadge status={gate ? (gate.ok ? "passed" : "warning") : "not_run"} />} />
        ))}
      </div>
      {gate && <ItemList emptyText="No blockers." items={gate.blockers.map((item) => <span key={item} className="danger-text">{redactReportText(item)}</span>)} />}
      {gate && <ItemList emptyText="No warnings." items={gate.warnings.map((item) => <span key={item}>{redactReportText(item)}</span>)} />}
    </section>
  );
}

function ModulePlaytestStressProPanel({
  modules,
  selectedModuleId,
  compatibilityMatrix,
  qualityGate,
  error,
  disabled,
  onSelectModule,
  onRunSelectedPlaytest,
  onRunCompatibilityStress,
  onRunQualityGate
}: {
  modules: ModuleBrowserSummary[];
  selectedModuleId: string;
  compatibilityMatrix: ModCompatibilityMatrix | null;
  qualityGate: ModQualityGateResult | null;
  error: string;
  disabled: boolean;
  onSelectModule: (packageId: string) => void;
  onRunSelectedPlaytest: () => void;
  onRunCompatibilityStress: () => void;
  onRunQualityGate: () => void;
}) {
  const selectedModule = modules.find((module) => module.package_id === selectedModuleId) ?? modules[0] ?? null;
  const matrixIssues = [
    ...(compatibilityMatrix?.conflicts_summary ?? []),
    ...(compatibilityMatrix?.entries ?? []).flatMap((entry) => [...entry.errors, ...entry.warnings])
  ].map(redactReportText);
  const namespaceConflicts = matrixIssues.filter((issue) => /namespace|state/i.test(issue));
  const migrationConflicts = [
    ...matrixIssues,
    ...(qualityGate?.blockers ?? []).map(redactReportText),
    ...(qualityGate?.warnings ?? []).map(redactReportText)
  ].filter((issue) => /migration|schema/i.test(issue));
  const hiddenLeakWarnings = [
    ...(qualityGate?.blockers ?? []).map(redactReportText).filter((issue) => /hidden|leak|secret/i.test(issue)),
    ...(qualityGate?.warnings ?? []).map(redactReportText).filter((issue) => /hidden|leak|secret/i.test(issue))
  ];
  const failedStep = qualityGate
    ? qualityGate.blockers[0]
      ? redactReportText(qualityGate.blockers[0])
      : "none"
    : "not run";
  const playtestPassed = Boolean(qualityGate?.ok);

  return (
    <section className="module-pro-panel" data-v35-module-playtest-stress="safe-summary">
      <h4>Module Playtest / Stress UI Pro</h4>
      <p className="muted">Local module playtest suites use declared rules and safe summaries only. No arbitrary code execution, no provider calls, no upload, no auto-fix, and no active GameState mutation.</p>
      <div className="button-row">
        <select value={selectedModule?.package_id ?? ""} onChange={(event) => onSelectModule(event.target.value)} disabled={disabled || modules.length === 0} aria-label="Module playtest suite">
          {modules.map((module) => (
            <option key={module.package_id} value={module.package_id}>{module.name} ({module.package_id})</option>
          ))}
        </select>
        <button type="button" onClick={onRunSelectedPlaytest} disabled={disabled || !selectedModule}>Run Selected Module Playtest</button>
        <button type="button" onClick={onRunCompatibilityStress} disabled={disabled}>Run Compatibility Stress</button>
        <button type="button" onClick={onRunQualityGate} disabled={disabled}>Run Module Quality Gate</button>
      </div>
      {error && <p className="error">{sanitizeDisplayError(error)}</p>}
      {modules.length === 0 ? (
        <EmptyState title="No module playtest suites loaded." detail="Refresh the local gameplay module debugger to load declared module actions. Missing data stays unavailable instead of being invented." />
      ) : (
        <div className="safe-summary-grid">
          <SafeSummaryCard title="Selected module" value={selectedModule?.package_id ?? "none"} detail={selectedModule?.name ?? "Choose a local module suite."} />
          <SafeSummaryCard title="Pass / fail" value={qualityGate ? (playtestPassed ? "pass" : "fail") : "not run"} detail="Based on local quality/playtest safe summary, redaction, and no-provider checks." />
          <SafeSummaryCard title="Failed step" value={failedStep} detail="Safe step label only; hidden details are not rendered." />
          <SafeSummaryCard title="Action coverage" value={selectedModule?.package_type === "action_mod" ? "declared action mod" : "safe package summary"} detail="Coverage is reported by local gates when available; UI does not execute module code." />
          <SafeSummaryCard title="State namespace conflicts" value={String(namespaceConflicts.length)} detail="Compatibility matrix safe summaries." />
          <SafeSummaryCard title="Migration conflicts" value={String(migrationConflicts.length)} detail="Schema/migration warnings from local gates." />
          <SafeSummaryCard title="Hidden leak warnings" value={String(hiddenLeakWarnings.length)} detail="No hidden text full content is shown." />
          <SafeSummaryCard title="Raw StateDelta" value="debug-gated only" detail="Normal module stress view never renders raw StateDelta payloads." />
        </div>
      )}
      {selectedModule && (
        <div className="mode-landing-grid">
          <FeatureCard title="Declared rules only" detail={`${selectedModule.package_type} package metadata is inspected without loading runtime code.`} status={<ValidationStatusBadge status={selectedModule.local_only ? "passed" : "warning"} />} />
          <FeatureCard title="Validation status" detail={selectedModule.validation_status} status={<ValidationStatusBadge status={selectedModule.validation_status === "valid" ? "passed" : "warning"} />} />
          <FeatureCard title="Hidden details" detail="Redacted from normal module QA view; debug-only details stay behind DebugGate." status={<ValidationStatusBadge status="passed" />} />
        </div>
      )}
      <div className="grid two-column">
        <div>
          <h5>Compatibility stress blockers / warnings</h5>
          <ItemList emptyText="No namespace, migration, or compatibility stress issue loaded." items={[...namespaceConflicts, ...migrationConflicts].map((issue, index) => <span key={`${issue}-${index}`}>{issue}</span>)} />
        </div>
        <div>
          <h5>Hidden leak warnings</h5>
          <ItemList emptyText="No hidden leak warning loaded." items={hiddenLeakWarnings.map((issue, index) => <span key={`${issue}-${index}`}>{issue}</span>)} />
        </div>
      </div>
      <p className="muted">Module playtest safe summary: quality gate and compatibility reports provide pass/fail, failed step, action coverage, namespace conflict, migration conflict, and hidden leak warning rows. Raw StateDelta payloads are not rendered in this normal QA view.</p>
    </section>
  );
}

function RuleModuleContractPanel() {
  return (
    <section className="module-pro-panel">
      <h4>Rule Module Contract UI</h4>
      <p className="muted">Rule Modules are contract-only in v3.4. This view reviews manifests, provided systems, state schema extensions, actions, rules, permissions, compatibility notes, and migration warnings without running module code.</p>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Runtime" value="contract-only" detail="No sandbox runtime, JS, Python, or arbitrary code execution." />
        <SafeSummaryCard title="Migration" value="warning required" detail="State schema extensions need migration review before local apply." />
      </div>
      <div className="permission-matrix">
        {DANGEROUS_MODULE_PERMISSIONS.map((permission) => (
          <div key={permission} className="permission-row blocked">
            <strong>{permission}</strong>
            <span>blocked</span>
            <small>Dangerous permission is denied by default and cannot be enabled from the frontend.</small>
          </div>
        ))}
      </div>
    </section>
  );
}

function ImportExportWizardProPanel() {
  const filtered = [".env", "API keys", "provider secrets", "database files", "logs/cache", "node_modules/dist", "debug reports", "mature/private content"];
  return (
    <section className="module-pro-panel">
      <h4>Import / Export Wizard Pro</h4>
      <p className="muted">Import is dry-run first; export previews safe manifests. No upload, no remote download, no online marketplace, no package execution.</p>
      <div className="mode-landing-grid">
        {["select local package", "validate manifest", "show permissions", "show compatibility", "quality gate status", "dry-run preview", "confirm import"].map((step) => (
          <FeatureCard key={step} title={step} detail="Required before local import apply." status={<ValidationStatusBadge status="not_run" />} />
        ))}
      </div>
      <ItemList emptyText="No filtering policy." items={filtered.map((item) => <span key={item}>{item} excluded by default</span>)} />
      <p className="muted">Provider Profile Pack export may contain api_key_env or secret_ref only, never a raw key.</p>
    </section>
  );
}

function AuthoringValidationDashboardPanel({ modules }: { modules: ModuleBrowserSummary[] }) {
  const blockers = modules.filter((module) => module.validation_status === "invalid" || module.errors.length > 0);
  return (
    <section className="module-pro-panel">
      <h4>Authoring Validation Dashboard</h4>
      <p className="muted">Central safe validation overview. No auto-fix, no LLM, no upload, no hidden/debug details.</p>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Overall authoring validation" value={blockers.length ? "blocked" : "review"} detail="Run dedicated validators before safe apply." />
        <SafeSummaryCard title="Module blockers" value={String(blockers.length)} detail="Local manifest blockers only." />
        <SafeSummaryCard title="Categories" value={String(AUTHORING_VALIDATION_CATEGORIES.length)} detail="World/script/character/mod/import-export coverage." />
      </div>
      <div className="mode-landing-grid">
        {AUTHORING_VALIDATION_CATEGORIES.map((category) => (
          <FeatureCard key={category} title={category} detail="Open the affected editor for safe issue details." status={<ValidationStatusBadge status={blockers.length ? "warning" : "not_run"} />} />
        ))}
      </div>
      <ItemList emptyText="No module validation blockers." items={blockers.map((module) => <span key={module.package_id} className="danger-text">{module.package_id}: {redactReportText(module.errors.join(", "))}</span>)} />
    </section>
  );
}

function AuthoringDiffPreview({ validationStatus, destructive }: { validationStatus: string; destructive: boolean }) {
  return (
    <section className="module-pro-panel">
      <h4>AuthoringDiffPreview</h4>
      <p className="muted">Dry-run result must be reviewed before apply/import/export. Normal preview excludes hidden facts, raw state_deltas, and secrets.</p>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Before / after" value="safe summary" detail="Raw YAML and hidden text are not shown here." />
        <SafeSummaryCard title="Changed entities" value="review" detail="Added, removed, modified counts appear after dry-run." />
        <SafeSummaryCard title="Validation" value={validationStatus} detail="Validation blockers prevent apply." />
        <SafeSummaryCard title="Destructive risk" value={destructive ? "high risk" : "not detected"} detail="Deletes/overwrites require explicit confirm." />
      </div>
    </section>
  );
}

function AuthoringAuditTrailPanel({ moduleAudit, crossModeAudit, riskFilter, resultFilter, onRiskFilterChange, onResultFilterChange, onJumpPackage }: {
  moduleAudit: ModAuditRecord[];
  crossModeAudit: CrossModeAuditRecord[];
  riskFilter: string;
  resultFilter: string;
  onRiskFilterChange: (value: string) => void;
  onResultFilterChange: (value: string) => void;
  onJumpPackage: (packageId: string) => void;
}) {
  const rows = [
    ...moduleAudit.map((record) => ({
      id: record.audit_id,
      timestamp: record.timestamp,
      actor: record.actor,
      action: record.action_type,
      entity: record.package_id,
      result: record.result,
      risk: record.risk_level,
      summary: record.safe_summary,
      source: "mod"
    })),
    ...crossModeAudit.map((record) => ({
      id: record.audit_id,
      timestamp: record.timestamp,
      actor: record.actor,
      action: record.action_type,
      entity: record.source_artifact_id ?? "cross-mode",
      result: record.result,
      risk: "low",
      summary: record.safe_summary,
      source: "cross-mode"
    }))
  ].filter((row) => (riskFilter === "all" || row.risk === riskFilter) && (resultFilter === "all" || row.result === resultFilter));
  return (
    <section className="module-pro-panel">
      <h4>Authoring Audit Trail UI</h4>
      <p className="muted">Local authoring audit is not EventLog. It does not upload, mutate GameState, or show raw state_deltas/secrets.</p>
      <div className="module-filter-grid">
        <label>
          Risk
          <select value={riskFilter} onChange={(event) => onRiskFilterChange(event.target.value)}>
            <option value="all">All</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="blocked">Blocked</option>
          </select>
        </label>
        <label>
          Result
          <select value={resultFilter} onChange={(event) => onResultFilterChange(event.target.value)}>
            <option value="all">All</option>
            <option value="success">Success</option>
            <option value="failure">Failure</option>
            <option value="rejected">Rejected</option>
            <option value="dry_run">Dry run</option>
          </select>
        </label>
      </div>
      <ItemList
        emptyText="No audit records match the filters."
        items={rows.slice(0, 12).map((row) => (
          <span key={row.id}>
            {row.timestamp} · {row.actor} · {row.action} · {row.entity} · {row.result} · {row.risk}: {row.summary}
            {row.source === "mod" && <button type="button" onClick={() => onJumpPackage(row.entity)}>Jump</button>}
          </span>
        ))}
      />
    </section>
  );
}

function AuthoringBackupRestorePanel() {
  const sections = ["world pack drafts", "script packs", "character packs", "mod packages", "validation reports safe summaries"];
  return (
    <section className="module-pro-panel">
      <h4>Authoring Backup / Restore UX</h4>
      <p className="muted">Authoring backups are local and dry-run first. Restore requires dry-run preview and explicit confirm.</p>
      <ItemList emptyText="No authoring backup sections." items={sections.map((section) => <span key={section}>{section}</span>)} />
      <p className="muted">Excluded by default: .env, API keys, provider secrets, logs/cache/build outputs, debug-only data, mature/private content.</p>
    </section>
  );
}

function SafeApplyWorkflowPanel({ canApply }: { canApply: boolean }) {
  const steps = ["select draft/package", "validate", "quality gate", "diff preview", "dry-run", "explicit confirm", "apply to local content pack/project files", "audit record"];
  return (
    <section className="module-pro-panel">
      <h4>Safe Apply / Publish-to-Local Workflow</h4>
      <p className="muted">Safe apply writes local content/project files only after validation, dry-run, and explicit confirm. It does not modify active GameState, upload, or call LLMs.</p>
      <div className="mode-landing-grid">
        {steps.map((step, index) => (
          <FeatureCard key={step} title={`${index + 1}. ${step}`} detail={step === "explicit confirm" ? "Required for apply/import/export." : "Safe summary step."} status={<ValidationStatusBadge status={canApply && index < 5 ? "passed" : "not_run"} />} />
        ))}
      </div>
      {!canApply && <p className="danger-text">Apply is blocked until validation, dry-run, and confirmation are complete. Secret-like content blocks apply.</p>}
    </section>
  );
}

function CrossModeDashboardPanel({
  drafts,
  timeline,
  links,
  conflicts,
  audit
}: {
  drafts: CrossModeDraftSummary[];
  timeline: CrossModeTimelineEntry[];
  links: CrossModeLinkReviewReport | null;
  conflicts: CrossModeConflictReport | null;
  audit: CrossModeAuditRecord[];
}) {
  const conflictCount = conflicts?.conflicts.length ?? 0;
  const pendingReview = drafts.filter((draft) => draft.status !== "applied").length;
  const [reviewedConflictIds, setReviewedConflictIds] = useState<string[]>([]);
  const [fixDrafts, setFixDrafts] = useState<Record<string, string>>({});
  const conflictRows = useMemo(() => buildCrossModeConflictRows(conflicts, links), [conflicts, links]);
  return (
    <section className="cross-mode-dashboard">
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Draft count" value={String(drafts.length)} detail="Drafts are not world facts." />
        <SafeSummaryCard title="Proposal count" value={String(drafts.filter((draft) => draft.artifact_type.includes("proposal")).length)} detail="Apply requires validation." />
        <SafeSummaryCard title="Pending review" value={String(pendingReview)} detail="Review rows show safe summaries only." />
        <SafeSummaryCard title="Conflict count" value={String(conflictCount)} detail="Conflicts do not auto-apply." />
        <SafeSummaryCard title="Recent audit" value={String(audit.length)} detail="Audit entries are safe summaries." />
        <SafeSummaryCard title="Timeline" value={String(timeline.length)} detail="Normal dashboard excludes raw state deltas." />
      </div>
      <div className="mode-landing-grid">
        {["Novel to World", "World to Novel", "Tavern to World", "World to Tavern", "Tavern to Novel", "Novel to Tavern"].map((direction) => (
          <FeatureCard
            key={direction}
            title={direction}
            detail="Draft/proposal lane. Validation and confirmation required before apply."
            status={<ValidationStatusBadge status={conflictCount ? "warning" : "not_run"} />}
          />
        ))}
      </div>
      {links && (
        <p className="muted">
          Link review: broken {links.broken_links.length}, hidden risk {links.hidden_target_risks.length}, duplicate {links.duplicate_links.length}.
        </p>
      )}
      <CrossModeConflictReviewPro
        rows={conflictRows}
        reviewedConflictIds={reviewedConflictIds}
        fixDrafts={fixDrafts}
        onMarkReviewed={(conflictId) => setReviewedConflictIds((current) => current.includes(conflictId) ? current : [...current, conflictId])}
        onCreateFixDraft={(conflict) => setFixDrafts((current) => ({
          ...current,
          [conflict.conflictId]: `Fix draft for ${conflict.category}: ${conflict.suggestedAction}. This local draft does not apply automatically.`
        }))}
        onJumpToRef={(ref) => {
          const target = document.querySelector(`[data-cross-mode-ref="${CSS.escape(ref)}"]`);
          target?.scrollIntoView({ behavior: "smooth", block: "center" });
        }}
      />
    </section>
  );
}

type CrossModeConflictReviewRow = {
  conflictId: string;
  category: string;
  severity: string;
  affectedRefs: string[];
  safeSummary: string;
  status: string;
  suggestedAction: string;
};

function CrossModeConflictReviewPro({
  rows,
  reviewedConflictIds,
  fixDrafts,
  onMarkReviewed,
  onCreateFixDraft,
  onJumpToRef
}: {
  rows: CrossModeConflictReviewRow[];
  reviewedConflictIds: string[];
  fixDrafts: Record<string, string>;
  onMarkReviewed: (conflictId: string) => void;
  onCreateFixDraft: (conflict: CrossModeConflictReviewRow) => void;
  onJumpToRef: (ref: string) => void;
}) {
  const categories = ["character identity", "timeline order", "relationship", "fact visibility", "stale link", "broken link", "proposal validation"];
  const groups = categories.map((category) => ({ category, rows: rows.filter((row) => row.category === category) }));
  const uncategorized = rows.filter((row) => !categories.includes(row.category));
  const allGroups = uncategorized.length ? [...groups, { category: "other", rows: uncategorized }] : groups;

  return (
    <section className="studio-section cross-mode-conflict-review">
      <div className="authoring-pane-header">
        <div>
          <h4>CrossMode Conflict Review Pro</h4>
          <p className="muted">Review Novel/Tavern/World conflicts, stale links, broken links, hidden target risks, and proposal validation issues. Fix drafts are local review notes only.</p>
        </div>
        <StatusBadge label={rows.length ? `${rows.length} conflict(s)` : "No conflicts"} enabled={rows.length === 0} />
      </div>
      {rows.length === 0 ? (
        <EmptyState title="No CrossMode conflicts." detail="Run Cross-Mode validation or conflict detection to refresh Novel/Tavern/World link health." />
      ) : (
        <div className="stack">
          {allGroups.map((group) => (
            <section className="tool-card" key={group.category}>
              <h5>{group.category}</h5>
              {group.rows.length === 0 ? (
                <p className="muted">No {group.category} conflicts.</p>
              ) : (
                <div className="safe-preview-list">
                  {group.rows.map((conflict) => {
                    const reviewed = reviewedConflictIds.includes(conflict.conflictId);
                    return (
                      <article className="diff-summary" key={conflict.conflictId}>
                        <div className="authoring-pane-header">
                          <div>
                            <strong>{conflict.severity}: {conflict.conflictId}</strong>
                            <p>{sanitizeDisplayError(conflict.safeSummary)}</p>
                          </div>
                          <StatusBadge label={reviewed ? "reviewed" : conflict.status} enabled={reviewed} />
                        </div>
                        <dl className="metadata-list">
                          <dt>Affected refs</dt>
                          <dd>
                            {conflict.affectedRefs.length
                              ? conflict.affectedRefs.map((ref) => <button key={ref} type="button" onClick={() => onJumpToRef(ref)}>{sanitizeDisplayError(ref)}</button>)
                              : "Safe refs unavailable"}
                          </dd>
                          <dt>Suggested action</dt>
                          <dd>{conflict.suggestedAction}</dd>
                        </dl>
                        <div className="button-row">
                          <button type="button" onClick={() => onMarkReviewed(conflict.conflictId)}>Mark reviewed</button>
                          <button type="button" onClick={() => onCreateFixDraft(conflict)}>Create fix draft</button>
                          {conflict.affectedRefs[0] && <button type="button" onClick={() => onJumpToRef(conflict.affectedRefs[0])}>Jump to source/target</button>}
                        </div>
                        {fixDrafts[conflict.conflictId] && <p className="muted">{fixDrafts[conflict.conflictId]}</p>}
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          ))}
        </div>
      )}
      <p className="muted">Hidden target details, hidden facts, NPC secrets, raw state_deltas, and API keys are not displayed. Review and fix drafts do not bypass CrossMode validation.</p>
    </section>
  );
}

function buildCrossModeConflictRows(conflicts: CrossModeConflictReport | null, links: CrossModeLinkReviewReport | null): CrossModeConflictReviewRow[] {
  const rows: CrossModeConflictReviewRow[] = (conflicts?.conflicts ?? []).map((conflict) => ({
    conflictId: conflict.conflict_id,
    category: crossModeConflictCategory(conflict.conflict_type),
    severity: conflict.severity,
    affectedRefs: (conflict.affected_refs ?? []).map((ref) => sanitizeDisplayError(ref)),
    safeSummary: sanitizeDisplayError(conflict.safe_summary || "CrossMode conflict requires review."),
    status: conflict.status,
    suggestedAction: crossModeSuggestedAction(conflict.conflict_type)
  }));
  for (const linkId of links?.broken_links ?? []) {
    rows.push({ conflictId: `broken_${linkId}`, category: "broken link", severity: "error", affectedRefs: [linkId], safeSummary: "CrossMode link points to a missing source or target.", status: "open", suggestedAction: "Repair missing source/target refs and rerun CrossMode validation." });
  }
  for (const linkId of links?.stale_links ?? []) {
    rows.push({ conflictId: `stale_${linkId}`, category: "stale link", severity: "warning", affectedRefs: [linkId], safeSummary: "CrossMode link is deprecated or stale.", status: "open", suggestedAction: "Refresh the link target or archive the stale link after review." });
  }
  for (const linkId of links?.hidden_target_risks ?? []) {
    rows.push({ conflictId: `hidden_${linkId}`, category: "fact visibility", severity: "error", affectedRefs: [linkId], safeSummary: "Hidden target risk detected; details are redacted in normal UI.", status: "open", suggestedAction: "Review in authoring/debug-safe context and keep hidden details out of normal cross-mode views." });
  }
  const seen = new Set<string>();
  return rows.filter((row) => {
    if (seen.has(row.conflictId)) return false;
    seen.add(row.conflictId);
    return true;
  });
}

function crossModeConflictCategory(conflictType: string): string {
  const normalized = conflictType.toLowerCase();
  if (normalized.includes("character") || normalized.includes("identity")) return "character identity";
  if (normalized.includes("timeline") || normalized.includes("order")) return "timeline order";
  if (normalized.includes("relationship")) return "relationship";
  if (normalized.includes("visibility") || normalized.includes("hidden") || normalized.includes("fact")) return "fact visibility";
  if (normalized.includes("stale") || normalized.includes("deprecated")) return "stale link";
  if (normalized.includes("broken") || normalized.includes("missing")) return "broken link";
  if (normalized.includes("proposal") || normalized.includes("validation") || normalized.includes("apply")) return "proposal validation";
  return "proposal validation";
}

function crossModeSuggestedAction(conflictType: string): string {
  const category = crossModeConflictCategory(conflictType);
  if (category === "character identity") return "Compare Novel/Tavern/World character refs and create a safe identity mapping draft.";
  if (category === "timeline order") return "Review timeline order and create a reorder proposal; do not rewrite EventLog.";
  if (category === "relationship") return "Review relationship refs and create a proposal for validation.";
  if (category === "fact visibility") return "Keep hidden target details redacted and rerun visibility validation before apply.";
  if (category === "stale link") return "Refresh or archive the stale CrossModeLink after validation.";
  if (category === "broken link") return "Repair missing source/target refs and rerun CrossMode validation.";
  return "Create a fix draft, validate it, and require explicit apply confirmation.";
}

function ProjectShell({
  projects,
  selectedProjectId,
  modeStatuses,
  error,
  message,
  onRefresh,
  onSelect,
  onCreate,
  onValidate
}: {
  projects: NarrativeProjectSummary[];
  selectedProjectId: string;
  modeStatuses: NarrativeProjectModeStatus[];
  error: string;
  message: string;
  onRefresh: () => void;
  onSelect: (projectId: string) => void;
  onCreate: (projectId: string, name: string, root: string) => void;
  onValidate: (projectId: string) => void;
}) {
  const [projectId, setProjectId] = useState("local_project");
  const [name, setName] = useState("Local Narrative Project");
  const [root, setRoot] = useState("projects/local_project");
  const [novelManuscripts, setNovelManuscripts] = useState<NovelManuscript[]>([]);
  const [novelChapters, setNovelChapters] = useState<NovelChapter[]>([]);
  const [novelScenes, setNovelScenes] = useState<NovelScene[]>([]);
  const [novelError, setNovelError] = useState("");
  const [novelMessage, setNovelMessage] = useState("");
  const [newManuscriptId, setNewManuscriptId] = useState("manuscript");
  const [newManuscriptTitle, setNewManuscriptTitle] = useState("Untitled Manuscript");
  const [newChapterTitle, setNewChapterTitle] = useState("Chapter One");
  const [selectedManuscriptId, setSelectedManuscriptId] = useState("");
  const [selectedChapterId, setSelectedChapterId] = useState("");
  const [chapterDraftText, setChapterDraftText] = useState("");
  const [chapterDraftSavedText, setChapterDraftSavedText] = useState("");
  const [novelSearchQuery, setNovelSearchQuery] = useState("");
  const [novelSearchStatus, setNovelSearchStatus] = useState("");
  const [novelSearchTag, setNovelSearchTag] = useState("");
  const [novelSearchResults, setNovelSearchResults] = useState<NovelSearchResult[]>([]);
  const [novelSnapshots, setNovelSnapshots] = useState<NovelDraftSnapshot[]>([]);
  const [novelSnapshotMessage, setNovelSnapshotMessage] = useState("");
  const [writingSession, setWritingSession] = useState<WritingSessionState | null>(null);
  const [novelPreferences, setNovelPreferences] = useState<NovelPreferences | null>(null);
  const [tavernCharacters, setTavernCharacters] = useState<TavernCharacter[]>([]);
  const [tavernSessions, setTavernSessions] = useState<TavernSession[]>([]);
  const [tavernMessages, setTavernMessages] = useState<TavernMessage[]>([]);
  const [tavernScenePresets, setTavernScenePresets] = useState<TavernScenePreset[]>([]);
  const [multiNPCScenes, setMultiNPCScenes] = useState<MultiNPCSceneSummary[]>([]);
  const [tavernPreferences, setTavernPreferences] = useState<TavernPreferences | null>(null);
  const [tavernRecoveryRecords, setTavernRecoveryRecords] = useState<TavernSessionRecoveryRecord[]>([]);
  const [tavernExportPreview, setTavernExportPreview] = useState<TavernSessionExportPreview | null>(null);
  const [rpSafetyDashboard, setRpSafetyDashboard] = useState<RPSafetyDashboardReport | null>(null);
  const [worldNpcSummaries, setWorldNpcSummaries] = useState<WorldNpcSafeSummary[]>([]);
  const [selectedWorldNpcId, setSelectedWorldNpcId] = useState("");
  const [worldNpcMode, setWorldNpcMode] = useState<"player_safe" | "authoring">("player_safe");
  const [worldNpcAdapterPreview, setWorldNpcAdapterPreview] = useState<Record<string, unknown> | null>(null);
  const [tavernError, setTavernError] = useState("");
  const [tavernMessage, setTavernMessage] = useState("");
  const [newTavernCharacterId, setNewTavernCharacterId] = useState("tavern_character");
  const [newTavernCharacterName, setNewTavernCharacterName] = useState("Tavern Character");
  const [newTavernSessionId, setNewTavernSessionId] = useState("tavern_session");
  const [newTavernSessionTitle, setNewTavernSessionTitle] = useState("Tavern Session");
  const [newMultiNPCSceneId, setNewMultiNPCSceneId] = useState("multi_npc_scene");
  const [newMultiNPCSceneTitle, setNewMultiNPCSceneTitle] = useState("Multi-NPC Scene");
  const [selectedMultiNPCSceneId, setSelectedMultiNPCSceneId] = useState("");
  const [selectedTavernCharacterId, setSelectedTavernCharacterId] = useState("");
  const [selectedTavernSessionId, setSelectedTavernSessionId] = useState("");
  const [tavernCardRaw, setTavernCardRaw] = useState('{"name":"Mira","description":"A local RP draft.","personality":"Careful and warm."}');
  const [chatInput, setChatInput] = useState("");
  const [chatSafetyNotes, setChatSafetyNotes] = useState<string[]>([]);
  const [newScenePresetId, setNewScenePresetId] = useState("quiet_evening");
  const [newScenePresetName, setNewScenePresetName] = useState("Quiet Evening");
  const [crossModeDrafts, setCrossModeDrafts] = useState<CrossModeDraftSummary[]>([]);
  const [crossModeTimeline, setCrossModeTimeline] = useState<CrossModeTimelineEntry[]>([]);
  const [crossModeLinks, setCrossModeLinks] = useState<CrossModeLinkReviewReport | null>(null);
  const [crossModeConflicts, setCrossModeConflicts] = useState<CrossModeConflictReport | null>(null);
  const [crossModeAudit, setCrossModeAudit] = useState<CrossModeAuditRecord[]>([]);
  const [crossModeError, setCrossModeError] = useState("");
  const [crossModeMessage, setCrossModeMessage] = useState("");
  const [crossModeSourceRef, setCrossModeSourceRef] = useState("novel:scene:scene_1");
  const [crossModeDraftType, setCrossModeDraftType] = useState("fact_draft");
  const [worldToNovelPreview, setWorldToNovelPreview] = useState<Record<string, unknown> | null>(null);
  const [tavernProposalId, setTavernProposalId] = useState("proposal_m1");
  const [modules, setModules] = useState<ModuleBrowserSummary[]>([]);
  const [selectedModuleId, setSelectedModuleId] = useState("");
  const [moduleDetail, setModuleDetail] = useState<ModuleBrowserDetail | null>(null);
  const [modulePermissions, setModulePermissions] = useState<ModulePermissionSummary | null>(null);
  const [modulePermissionSummaries, setModulePermissionSummaries] = useState<ModulePermissionSummary[]>([]);
  const [moduleCompatibility, setModuleCompatibility] = useState<Record<string, unknown> | null>(null);
  const [moduleMatrix, setModuleMatrix] = useState<ModCompatibilityMatrix | null>(null);
  const [moduleQualityGate, setModuleQualityGate] = useState<ModQualityGateResult | null>(null);
  const [moduleAudit, setModuleAudit] = useState<ModAuditRecord[]>([]);
  const [moduleError, setModuleError] = useState("");
  const [moduleMessage, setModuleMessage] = useState("");
  const [moduleRiskFilter, setModuleRiskFilter] = useState("all");
  const [moduleTypeFilter, setModuleTypeFilter] = useState("all");
  const [moduleValidationFilter, setModuleValidationFilter] = useState("all");
  const [moduleCertificationFilter, setModuleCertificationFilter] = useState("all");
  const [moduleSearchQuery, setModuleSearchQuery] = useState("");
  const [moduleCertificationLevel, setModuleCertificationLevel] = useState("");
  const [auditRiskFilter, setAuditRiskFilter] = useState("all");
  const [auditResultFilter, setAuditResultFilter] = useState("all");
  const selected = projects.find((project) => project.project_id === selectedProjectId) ?? null;
  const novel = modeStatuses.find((status) => status.mode === "novel");
  const tavern = modeStatuses.find((status) => status.mode === "tavern");
  const selectedChapter = novelChapters.find((chapter) => chapter.chapter_id === selectedChapterId) ?? null;
  const novelQualityIssues = useMemo(() => buildNovelQualityIssues(novelChapters, novelScenes), [novelChapters, novelScenes]);
  const chapterCurrentWordCount = chapterDraftText.split(/\s+/).filter(Boolean).length;

  async function loadNovelData() {
    if (!selectedProjectId) {
      return;
    }
    setNovelError("");
    try {
      const [manuscripts, chapters, scenes] = await Promise.all([
        fetchNovelManuscripts(selectedProjectId),
        fetchNovelChapters(selectedProjectId),
        fetchNovelScenes(selectedProjectId)
      ]);
      setNovelManuscripts(manuscripts.manuscripts);
      setNovelChapters(chapters.chapters);
      setNovelScenes(scenes.scenes);
      const firstManuscript = manuscripts.manuscripts[0]?.manuscript_id ?? "";
      const firstChapter = chapters.chapters[0]?.chapter_id ?? "";
      setSelectedManuscriptId((current) => current || firstManuscript);
      setSelectedChapterId((current) => current || firstChapter);
      const selectedChapter = chapters.chapters.find((chapter) => chapter.chapter_id === (selectedChapterId || firstChapter));
      const draftText = selectedChapter?.draft_text ?? "";
      setChapterDraftText(draftText);
      setChapterDraftSavedText(draftText);
      if (firstChapter) {
        const snapshots = await fetchNovelDraftSnapshots(selectedProjectId, selectedChapter?.chapter_id ?? firstChapter);
        setNovelSnapshots(snapshots.snapshots);
      } else {
        setNovelSnapshots([]);
      }
      const [session, preferences] = await Promise.all([
        fetchCurrentNovelWritingSession(selectedProjectId, firstManuscript),
        fetchNovelPreferences(selectedProjectId)
      ]);
      setWritingSession(session.session);
      setNovelPreferences(preferences);
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  useEffect(() => {
    void loadNovelData();
  }, [selectedProjectId]);

  async function loadTavernData() {
    if (!selectedProjectId) {
      return;
    }
    setTavernError("");
    try {
      const [characters, sessions, presets, multiScenes] = await Promise.all([
        fetchTavernCharacters(selectedProjectId),
        fetchTavernSessions(selectedProjectId),
        fetchTavernScenePresets(selectedProjectId),
        fetchTavernMultiNPCScenes(selectedProjectId)
      ]);
      setTavernCharacters(characters.characters);
      setTavernSessions(sessions.sessions);
      setTavernScenePresets(presets.scene_presets);
      setMultiNPCScenes(multiScenes.scenes);
      const [preferences, recovery, safety, npcs] = await Promise.allSettled([
        fetchTavernPreferences(selectedProjectId),
        fetchTavernRecoveryRecords(selectedProjectId),
        fetchRPSafetyDashboard(selectedProjectId),
        fetchWorldNpcSafeSummaries(selectedProjectId)
      ]);
      if (preferences.status === "fulfilled") setTavernPreferences(preferences.value);
      if (recovery.status === "fulfilled") setTavernRecoveryRecords(recovery.value.records);
      if (safety.status === "fulfilled") setRpSafetyDashboard(safety.value);
      if (npcs.status === "fulfilled") {
        setWorldNpcSummaries(npcs.value.npcs);
        setSelectedWorldNpcId((current) => current || npcs.value.npcs[0]?.npc_id || "");
      }
      const firstCharacter = characters.characters[0]?.tavern_character_id ?? "";
      const firstSession = sessions.sessions[0]?.session_id ?? "";
      setSelectedTavernCharacterId((current) => current || firstCharacter);
      setSelectedTavernSessionId((current) => current || firstSession);
      setSelectedMultiNPCSceneId((current) => current || multiScenes.scenes[0]?.scene_id || "");
      if (firstSession) {
        const messages = await fetchTavernMessages(selectedProjectId, selectedTavernSessionId || firstSession);
        setTavernMessages(messages.messages);
      } else {
        setTavernMessages([]);
      }
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  useEffect(() => {
    void loadTavernData();
  }, [selectedProjectId]);

  async function loadCrossModeData() {
    if (!selectedProjectId) {
      return;
    }
    setCrossModeError("");
    try {
      const [drafts, timeline, links, conflicts, audit] = await Promise.all([
        fetchNovelToWorldDrafts(selectedProjectId),
        fetchCrossModeTimeline(selectedProjectId),
        fetchCrossModeLinks(selectedProjectId),
        detectCrossModeConflicts(selectedProjectId),
        fetchCrossModeAudit(selectedProjectId)
      ]);
      setCrossModeDrafts(drafts.drafts);
      setCrossModeTimeline(timeline.entries);
      setCrossModeLinks(links);
      setCrossModeConflicts(conflicts);
      setCrossModeAudit(audit.audit);
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  useEffect(() => {
    void loadCrossModeData();
  }, [selectedProjectId]);

  async function loadModuleData(nextModuleId = selectedModuleId) {
    if (!selectedProjectId) {
      return;
    }
    setModuleError("");
    try {
      const [moduleList, permissions, matrix, audit] = await Promise.all([
        fetchProjectModules(selectedProjectId),
        fetchProjectModulePermissionsSummary(selectedProjectId),
        buildProjectModuleCompatibilityMatrix(selectedProjectId),
        fetchProjectModuleAudit(selectedProjectId)
      ]);
      setModules(moduleList.modules);
      setModulePermissionSummaries(permissions.permissions);
      setModuleMatrix(matrix.matrix);
      setModuleAudit(audit.records);
      const next = nextModuleId || moduleList.modules[0]?.package_id || "";
      setSelectedModuleId(next);
      if (next) {
        const [detail, modulePermission, compatibility] = await Promise.all([
          fetchProjectModule(selectedProjectId, next),
          fetchProjectModulePermissions(selectedProjectId, next),
          fetchProjectModuleCompatibility(selectedProjectId, next)
        ]);
        setModuleDetail(detail.module);
        setModulePermissions(modulePermission.permissions);
        setModuleCompatibility(compatibility.compatibility);
      } else {
        setModuleDetail(null);
        setModulePermissions(null);
        setModuleCompatibility(null);
      }
    } catch (err) {
      setModules([]);
      setModuleError(toErrorMessage(err));
    }
  }

  useEffect(() => {
    void loadModuleData();
  }, [selectedProjectId]);

  async function handleScanModules() {
    setModuleError("");
    setModuleMessage("");
    try {
      const report = await scanProjectModules(selectedProjectId);
      setModules(report.modules);
      setModuleMessage(`Scanned ${report.modules.length} local modules. ${report.errors.length} scan issue(s). No package code was executed.`);
      await loadModuleData(report.modules[0]?.package_id || selectedModuleId);
    } catch (err) {
      setModuleError(toErrorMessage(err));
    }
  }

  async function handleSelectModule(packageId: string) {
    setSelectedModuleId(packageId);
    setModuleCertificationLevel("");
    await loadModuleData(packageId);
  }

  async function handleValidateModule() {
    if (!selectedModuleId) {
      return;
    }
    setModuleError("");
    setModuleMessage("");
    try {
      const result = await validateProjectModule(selectedProjectId, selectedModuleId);
      setModuleMessage(result.validation.ok ? "Module validation passed." : `Module validation failed: ${result.validation.errors.length} blockers.`);
      await loadModuleData(selectedModuleId);
    } catch (err) {
      setModuleError(toErrorMessage(err));
    }
  }

  async function handleCertifyModule() {
    if (!selectedModuleId) {
      return;
    }
    setModuleError("");
    setModuleMessage("");
    try {
      const report = await certifyProjectModule(selectedProjectId, selectedModuleId);
      setModuleCertificationLevel(report.certification.level);
      setModuleMessage(`Certification: ${report.certification.level}. This is local advisory certification only.`);
      await loadModuleData(selectedModuleId);
    } catch (err) {
      setModuleError(toErrorMessage(err));
    }
  }

  async function handleModuleQualityGate() {
    if (!selectedModuleId) {
      return;
    }
    setModuleError("");
    setModuleMessage("");
    try {
      const report = await runProjectModuleQualityGate(selectedProjectId, selectedModuleId);
      setModuleQualityGate(report.quality_gate);
      setModuleCertificationLevel(report.quality_gate.certification_level);
      setModuleMessage(report.quality_gate.ok ? "Mod Quality Gate passed." : "Mod Quality Gate found blockers.");
      await loadModuleData(selectedModuleId);
    } catch (err) {
      setModuleError(toErrorMessage(err));
    }
  }

  async function handleModulePlaytestGate() {
    if (!selectedModuleId) {
      return;
    }
    await handleModuleQualityGate();
    setModuleMessage("Selected module playtest safe summary refreshed through local quality gates. No package code was executed.");
  }

  async function handleModuleCompatibilityStressSummary() {
    setModuleError("");
    setModuleMessage("");
    try {
      await loadModuleData(selectedModuleId);
      setModuleMessage("Module compatibility stress summaries refreshed. No package code was executed.");
    } catch (err) {
      setModuleError(toErrorMessage(err));
    }
  }

  async function handleCreateManuscript() {
    setNovelError("");
    setNovelMessage("");
    try {
      const manuscript = await createNovelManuscript(selectedProjectId, { manuscript_id: newManuscriptId, title: newManuscriptTitle });
      setNovelMessage("Manuscript created. It is a Novel draft container, not World state.");
      setSelectedManuscriptId(manuscript.manuscript_id);
      await loadNovelData();
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleCreateChapter() {
    setNovelError("");
    setNovelMessage("");
    try {
      const chapterId = `chapter_${novelChapters.length + 1}`;
      const chapter = await createNovelChapter(selectedProjectId, {
        chapter_id: chapterId,
        manuscript_id: selectedManuscriptId || novelManuscripts[0]?.manuscript_id,
        title: newChapterTitle,
        order_index: novelChapters.length
      });
      setNovelMessage("Chapter draft created. It does not modify GameState.");
      setSelectedChapterId(chapter.chapter_id);
      await loadNovelData();
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleSaveChapterDraft() {
    if (!selectedChapterId) {
      return;
    }
    setNovelError("");
    setNovelMessage("");
    try {
      await updateNovelChapter(selectedProjectId, selectedChapterId, { draft_text: chapterDraftText });
      setChapterDraftSavedText(chapterDraftText);
      setNovelMessage("Chapter draft saved locally.");
      await loadNovelData();
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleCreateScene() {
    if (!selectedChapterId) {
      return;
    }
    setNovelError("");
    setNovelMessage("");
    try {
      await createNovelScene(selectedProjectId, { scene_id: `scene_${novelScenes.length + 1}`, chapter_id: selectedChapterId, title: "New Scene" });
      setNovelMessage("Scene draft created.");
      await loadNovelData();
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleExport(format: "markdown" | "txt") {
    const manuscriptId = selectedManuscriptId || novelManuscripts[0]?.manuscript_id;
    if (!manuscriptId) {
      return;
    }
    if (!confirmDangerousAction("Export this Novel draft locally? Default filtering excludes authoring notes, hidden refs, mature/private content, debug data, raw state_deltas, provider secrets, and API keys.")) {
      return;
    }
    setNovelError("");
    setNovelMessage("");
    try {
      const result = await exportNovelManuscript(selectedProjectId, { manuscript_id: manuscriptId, format });
      setNovelMessage(`Novel ${format} export created with ${result.chapters_exported.length} chapter(s).`);
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleCreateSnapshot() {
    if (!selectedChapterId) {
      return;
    }
    setNovelError("");
    setNovelSnapshotMessage("");
    try {
      await createNovelDraftSnapshot(selectedProjectId, {
        target_type: "chapter",
        target_id: selectedChapterId,
        title: `Snapshot for ${selectedChapter?.title ?? selectedChapterId}`
      });
      const snapshots = await fetchNovelDraftSnapshots(selectedProjectId, selectedChapterId);
      setNovelSnapshots(snapshots.snapshots);
      setNovelSnapshotMessage("Draft snapshot created locally. Hidden context and API keys are not stored.");
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleCompareSnapshot(snapshotId: string) {
    setNovelError("");
    try {
      const result = await compareNovelDraftSnapshots(selectedProjectId, { left_snapshot_id: snapshotId, current_text: chapterDraftText });
      setNovelSnapshotMessage(`${result.safe_summary} Added lines ${result.added_lines}, removed lines ${result.removed_lines}.`);
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleStartWritingSession() {
    const manuscriptId = selectedManuscriptId || novelManuscripts[0]?.manuscript_id;
    if (!manuscriptId) {
      return;
    }
    setNovelError("");
    try {
      const session = await startNovelWritingSession(selectedProjectId, {
        session_id: `writing_${Date.now()}`,
        manuscript_id: manuscriptId,
        active_chapter_id: selectedChapterId || undefined,
        local_goal_words: 500
      });
      setWritingSession(session);
      setNovelMessage("Writing session started locally. No telemetry is uploaded.");
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleEndWritingSession() {
    if (!writingSession) {
      return;
    }
    setNovelError("");
    try {
      const ended = await endNovelWritingSession(selectedProjectId, writingSession.session_id);
      setWritingSession(ended);
      setNovelMessage("Writing session ended locally.");
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleNovelSearch(nextQuery = novelSearchQuery, nextStatus = novelSearchStatus, nextTag = novelSearchTag) {
    setNovelSearchQuery(nextQuery);
    setNovelSearchStatus(nextStatus);
    setNovelSearchTag(nextTag);
    if (!selectedProjectId) {
      return;
    }
    try {
      const result = await searchNovel(selectedProjectId, {
        keyword: nextQuery,
        status: nextStatus || undefined,
        tag: nextTag || undefined,
        chapter_id: selectedChapterId || undefined
      });
      setNovelSearchResults(result.results);
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleSaveNovelPreferences() {
    setNovelError("");
    try {
      const saved = await saveNovelPreferences(selectedProjectId, {
        default_manuscript_id: selectedManuscriptId || null,
        default_export_format: novelPreferences?.default_export_format ?? "markdown",
        show_word_count: true,
        show_world_bible_sidebar: true,
        show_timeline_panel: true,
        autosave_reminder_enabled: true,
        default_prompt_profile_id: novelPreferences?.default_prompt_profile_id ?? null
      });
      setNovelPreferences(saved);
      setNovelMessage("Novel preferences saved locally without secrets.");
    } catch (err) {
      setNovelError(toErrorMessage(err));
    }
  }

  async function handleCreateTavernCharacter() {
    setTavernError("");
    setTavernMessage("");
    try {
      const character = await createTavernCharacter(selectedProjectId, {
        tavern_character_id: newTavernCharacterId,
        display_name: newTavernCharacterName,
        description: "Project-local Tavern character draft."
      });
      setSelectedTavernCharacterId(character.tavern_character_id);
      setTavernMessage("Tavern character draft created. It does not modify World NPCs.");
      await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleImportTavernCard() {
    setTavernError("");
    setTavernMessage("");
    try {
      const result = await importTavernCharacterCard(selectedProjectId, tavernCardRaw);
      setSelectedTavernCharacterId(result.tavern_character.tavern_character_id);
      setTavernMessage(`Character card imported as a Tavern draft. ${result.warnings?.length ?? 0} warning(s).`);
      await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateTavernSession() {
    setTavernError("");
    setTavernMessage("");
    try {
      const session = await createTavernSession(selectedProjectId, {
        session_id: newTavernSessionId,
        title: newTavernSessionTitle,
        character_ids: selectedTavernCharacterId ? [selectedTavernCharacterId] : []
      });
      setSelectedTavernSessionId(session.session_id);
      setTavernMessage("Tavern session created. RP output remains project-local.");
      await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateMultiNPCScene() {
    if (!selectedProjectId) {
      return;
    }
    const participantIds = tavernCharacters.slice(0, 3).map((character) => character.tavern_character_id);
    setTavernError("");
    setTavernMessage("");
    try {
      const scene = await createTavernMultiNPCScene(selectedProjectId, {
        scene_id: newMultiNPCSceneId,
        title: newMultiNPCSceneTitle,
        participant_ids: participantIds,
        turn_order: participantIds
      });
      setSelectedMultiNPCSceneId(scene.scene_id);
      setTavernMessage("Multi-NPC scene created. It stores Tavern messages only and does not modify World GameState.");
      await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleGenerateMultiNPCReply() {
    if (!selectedProjectId || !selectedMultiNPCSceneId) {
      return;
    }
    setTavernError("");
    setTavernMessage("");
    try {
      const result = await generateTavernMultiNPCReply(selectedProjectId, selectedMultiNPCSceneId);
      setTavernMessage(`Generated safe local reply for ${result.message.speaker_id ?? "next speaker"}. World GameState unchanged.`);
      const scenes = await fetchTavernMultiNPCScenes(selectedProjectId);
      setMultiNPCScenes(scenes.scenes);
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleSendTavernMessage() {
    if (!selectedTavernSessionId || !selectedTavernCharacterId || !chatInput.trim()) {
      return;
    }
    setTavernError("");
    setTavernMessage("");
    try {
      const response = await sendTavernChatMessage(selectedProjectId, selectedTavernSessionId, {
        character_id: selectedTavernCharacterId,
        user_message: chatInput
      });
      setChatInput("");
      setChatSafetyNotes(response.safety_notes ?? []);
      setTavernMessage("Generated Tavern reply saved as a Tavern message only.");
      const messages = await fetchTavernMessages(selectedProjectId, selectedTavernSessionId);
      setTavernMessages(messages.messages);
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateScenePreset() {
    setTavernError("");
    setTavernMessage("");
    try {
      await createTavernScenePreset(selectedProjectId, {
        preset_id: newScenePresetId,
        name: newScenePresetName,
        description: "Style-only Tavern scene mood preset.",
        mood_tags: ["quiet", "local"]
      });
      setTavernMessage("Scene mood preset created. It affects style only.");
      await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleSaveTavernPreferences() {
    setTavernError("");
    setTavernMessage("");
    try {
      const saved = await saveTavernPreferences(selectedProjectId, {
        default_character_id: selectedTavernCharacterId || null,
        default_session_id: selectedTavernSessionId || null,
        default_prompt_profile_id: tavernPreferences?.default_prompt_profile_id ?? null,
        default_provider_profile_id: tavernPreferences?.default_provider_profile_id ?? null,
        show_rp_memory_panel: tavernPreferences?.show_rp_memory_panel ?? true,
        show_emotion_panel: tavernPreferences?.show_emotion_panel ?? true,
        show_relationship_tone_panel: tavernPreferences?.show_relationship_tone_panel ?? true,
        default_scene_mood_preset_id: tavernPreferences?.default_scene_mood_preset_id ?? tavernScenePresets[0]?.preset_id ?? null,
        mature_module_visible: false
      });
      setTavernPreferences(saved);
      setTavernMessage("Tavern preferences saved locally without secrets. Mature Module visibility remains off by default.");
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateTavernRecoveryDraft() {
    if (!selectedTavernSessionId || !chatInput.trim()) {
      return;
    }
    setTavernError("");
    try {
      const record = await createTavernRecoveryRecord(selectedProjectId, {
        record_id: `message_${Date.now()}`,
        target_type: "message",
        target_id: selectedTavernSessionId,
        safe_draft_text: chatInput,
        safe_metadata: { local_only: true, source: "chat_input" }
      });
      setTavernRecoveryRecords((records) => [record, ...records]);
      setTavernMessage("Local Tavern recovery draft created. Hidden context, mature/private content, raw prompts, and API keys are excluded.");
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handlePreviewTavernExport() {
    setTavernError("");
    try {
      const preview = await previewTavernSessionExport(selectedProjectId, {
        scope: selectedTavernSessionId ? "current_session" : "all_sessions",
        session_ids: selectedTavernSessionId ? [selectedTavernSessionId] : [],
        format: "json_safe"
      });
      setTavernExportPreview(preview);
      setTavernMessage("Tavern export preview generated. No file was written.");
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateTavernExport() {
    if (!confirmDangerousAction("Export selected Tavern sessions locally? Default filtering excludes API keys, hidden facts, NPC secrets, mature/private memory, debug data, raw prompts, and raw state_deltas.")) {
      return;
    }
    setTavernError("");
    try {
      const result = await createTavernSessionExport(selectedProjectId, {
        scope: selectedTavernSessionId ? "current_session" : "all_sessions",
        session_ids: selectedTavernSessionId ? [selectedTavernSessionId] : [],
        format: "json_safe",
        explicit_confirm: true
      });
      setTavernExportPreview(result);
      setTavernMessage(`Tavern export ${result.export_id} created locally. Nothing was uploaded.`);
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleRunRPSafety() {
    setTavernError("");
    try {
      const report = await runRPSafetyDashboard(selectedProjectId);
      setRpSafetyDashboard(report);
      setTavernMessage(`RP Safety Dashboard ${report.overall_status}: ${report.blocker_count} blocker(s), ${report.warning_count} warning(s).`);
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleAdaptWorldNpc(apply = false) {
    if (!selectedWorldNpcId) return;
    if (apply && !confirmDangerousAction("Create Tavern draft from this World NPC? This does not modify the World NPC or GameState.")) {
      return;
    }
    setTavernError("");
    try {
      const result = await adaptWorldNpcToTavern(selectedProjectId, { npc_id: selectedWorldNpcId, mode: worldNpcMode, apply });
      setWorldNpcAdapterPreview(result);
      setTavernMessage(apply ? "World NPC adapted into a Tavern draft. World NPC unchanged." : "World NPC to Tavern preview generated safely.");
      if (apply) await loadTavernData();
    } catch (err) {
      setTavernError(toErrorMessage(err));
    }
  }

  async function handleCreateCrossModeDraft() {
    setCrossModeError("");
    setCrossModeMessage("");
    try {
      const draft = await createNovelToWorldDraft(selectedProjectId, {
        source_ref: crossModeSourceRef,
        draft_type: crossModeDraftType,
        proposed_content: { source_ref: crossModeSourceRef, note: "UI review draft; not applied to World." }
      });
      setCrossModeMessage(`Cross-mode draft ${draft.artifact_id} created. It does not modify World state.`);
      await loadCrossModeData();
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  async function handleValidateCrossModeDraft(draftId: string) {
    setCrossModeError("");
    setCrossModeMessage("");
    try {
      const draft = await validateNovelToWorldDraft(selectedProjectId, draftId);
      setCrossModeMessage(`Draft ${draft.artifact_id} validation status: ${draft.validation_status ?? "checked"}.`);
      await loadCrossModeData();
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  async function handlePreviewWorldToNovel() {
    setCrossModeError("");
    setCrossModeMessage("");
    try {
      const preview = await previewWorldToNovel(selectedProjectId, {
        safe_event_summaries: ["A player-visible world event summary can become a Novel draft preview."],
        source_event_ids: ["event_preview"]
      });
      setWorldToNovelPreview(preview);
      setCrossModeMessage("World to Novel preview created. It did not write EventLog or GameState.");
      await loadCrossModeData();
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  async function handleValidateCrossMode() {
    setCrossModeError("");
    setCrossModeMessage("");
    try {
      const report = await validateCrossMode(selectedProjectId);
      setCrossModeMessage(`Cross-mode validation ${report.ok ? "passed" : "failed"}: ${String(report.summary?.errors ?? 0)} error(s), ${String(report.summary?.warnings ?? 0)} warning(s).`);
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  async function handleBuildTavernApplyPlan() {
    setCrossModeError("");
    setCrossModeMessage("");
    try {
      const plan = await buildTavernApplyPlan(selectedProjectId, tavernProposalId);
      setCrossModeMessage(`Apply plan ${String(plan.apply_plan_id ?? "")} created for review. Confirmation is still required.`);
      await loadCrossModeData();
    } catch (err) {
      setCrossModeError(toErrorMessage(err));
    }
  }

  return (
    <div className="studio-page">
      <PageHeader
        eyebrow="v2.1 Unified Narrative Project Layer"
        title="NarrativeProject Shell"
        description="Local project container for Novel drafts, Tavern proposals, World play, scripts, providers, and quality reports."
        actions={<button type="button" onClick={onRefresh}>Refresh</button>}
      />
      <ErrorPanel message={error} />
      <SuccessPanel message={message} />
      <section className="card-grid">
        <div className="tool-card">
          <h3>Projects</h3>
          {projects.length === 0 ? (
            <EmptyState title="No NarrativeProject found." detail="Create a local project shell. This does not modify active GameState." />
          ) : (
            <select value={selectedProjectId} onChange={(event) => onSelect(event.target.value)}>
              {projects.map((project) => (
                <option key={project.project_id} value={project.project_id}>{project.name}</option>
              ))}
            </select>
          )}
          {selected && (
            <p className="muted">
              {selected.project_id} · {selected.schema_version ?? "schema"} · {selected.safe_status ?? "ok"}
            </p>
          )}
          <button type="button" disabled={!selectedProjectId} onClick={() => onValidate(selectedProjectId)}>Validate Project</button>
        </div>
        <div className="tool-card">
          <h3>Create Project</h3>
          <label>
            Project id
            <input value={projectId} onChange={(event) => setProjectId(event.target.value)} />
          </label>
          <label>
            Name
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label>
            Local root
            <input value={root} onChange={(event) => setRoot(event.target.value)} />
          </label>
          <button type="button" onClick={() => onCreate(projectId, name, root)}>Create</button>
        </div>
      </section>
      <section className="card-grid">
        <ProjectModeCard title="Novel" status={novel} message="Novel Studio MVP coming in v2.2; local manuscripts, chapters, scenes, and safe export are now available." />
        <ProjectModeCard title="Tavern" status={tavern} message="Tavern Studio MVP coming in v2.3" />
        {modeStatuses.filter((status) => !["novel", "tavern"].includes(status.mode)).map((status) => (
          <ProjectModeCard key={status.mode} title={status.mode} status={status} message="Project mode entry is routed through the v2.1 Mode Router." />
        ))}
      </section>
      <section className="mode-landing-grid">
        <ModeLandingPage
          title="Novel Studio"
          localStatus="Project-local drafts"
          features={["Manuscripts", "Outlines", "Chapters", "Scenes", "Character arcs", "Plot threads", "Foreshadowing", "Exports", "World to Novel imports"]}
          warnings={["Hidden World facts are not displayed in normal Novel UI.", "Drafts do not modify GameState."]}
          actions={["Create manuscript", "Open outline", "Open chapter editor", "Run novel quality", "Export draft"]}
        />
        <ModeLandingPage
          title="Tavern Studio"
          localStatus="RP expression layer"
          features={["Characters", "Sessions", "Single-character chat", "Multi-NPC scenes", "RP memory", "Emotion", "Relationship tone", "Scene mood", "Voice Lab"]}
          warnings={["Tavern does not directly modify World state.", "Mature Module is disabled by default."]}
          actions={["Import character card", "Create session", "Open chat", "Open multi-NPC scene", "Open RP safety settings"]}
        />
        <ModeLandingPage
          title="Cross-Mode Bridge"
          localStatus="Proposal and validation flow"
          features={["Novel to World", "World to Novel", "Tavern to World", "World to Tavern", "Tavern to Novel", "Novel to Tavern"]}
          warnings={["Apply requires validation and confirmation.", "Raw state deltas are not shown in normal review."]}
          actions={["Review drafts", "Validate bridge", "Inspect conflicts", "Open audit"]}
        />
      </section>
      <section className="tool-card">
        <h3>Novel Studio UI Pro</h3>
        <p className="muted">Novel drafts remain project-local and never write World GameState. Hidden facts, raw env, API keys, private notes, raw prompts, and raw state_deltas are not shown in normal Novel UI.</p>
        <ErrorPanel message={novelError} compact />
        <SuccessPanel message={novelMessage} compact />
        <SuccessPanel message={novelSnapshotMessage} compact />
        <div className="form-grid">
          <label>
            Manuscript id
            <input value={newManuscriptId} onChange={(event) => setNewManuscriptId(event.target.value)} />
          </label>
          <label>
            Manuscript title
            <input value={newManuscriptTitle} onChange={(event) => setNewManuscriptTitle(event.target.value)} />
          </label>
          <button type="button" disabled={!selectedProjectId} onClick={handleCreateManuscript}>Create Manuscript</button>
          <button type="button" disabled={!selectedManuscriptId} onClick={handleStartWritingSession}>Start Writing Session</button>
          <button type="button" disabled={!writingSession || Boolean(writingSession.ended_at)} onClick={handleEndWritingSession}>End Session</button>
          <button type="button" disabled={!selectedProjectId} onClick={handleSaveNovelPreferences}>Save Novel Preferences</button>
        </div>
        <NovelWorkspaceShell
          navigation={(
            <div className="stack">
              <strong>Novel Workspace</strong>
              {["Manuscript", "Outline", "Chapters", "Scenes", "Characters", "Plot", "Foreshadowing", "Timeline", "World Bible", "Search", "Export", "Quality"].map((item) => (
                <span key={item}>{item}</span>
              ))}
            </div>
          )}
          main={(
            <div className="stack">
              <ManuscriptDashboard manuscripts={novelManuscripts} chapters={novelChapters} scenes={novelScenes} />
              {novelManuscripts.length === 0 ? (
                <EmptyState title="No manuscripts yet." detail="Create a manuscript to begin outlining and drafting." />
              ) : (
                <div className="novel-card-list">
                  {novelManuscripts.map((manuscript) => (
                    <ManuscriptCard
                      key={manuscript.manuscript_id}
                      manuscript={manuscript}
                      selected={manuscript.manuscript_id === selectedManuscriptId}
                      onSelect={() => setSelectedManuscriptId(manuscript.manuscript_id)}
                    />
                  ))}
                </div>
              )}
              <NovelSearchFilterBar
                value={novelSearchQuery}
                status={novelSearchStatus}
                tag={novelSearchTag}
                onChange={(value) => void handleNovelSearch(value, novelSearchStatus, novelSearchTag)}
                onStatusChange={(value) => void handleNovelSearch(novelSearchQuery, value, novelSearchTag)}
                onTagChange={(value) => void handleNovelSearch(novelSearchQuery, novelSearchStatus, value)}
              />
              {novelSearchResults.length > 0 && (
                <ItemList
                  emptyText="No search results"
                  items={novelSearchResults.map((result) => (
                    <span key={`${result.result_type}-${result.result_id}`}>{result.result_type}: {result.title} · {result.status}</span>
                  ))}
                />
              )}
              <div className="card-grid">
                <div>
                  <NovelToolbar
                    title="Chapters"
                    actions={<><input value={newChapterTitle} onChange={(event) => setNewChapterTitle(event.target.value)} /><button type="button" disabled={!selectedManuscriptId} onClick={handleCreateChapter}>Add Chapter</button></>}
                  />
                  <div className="novel-card-list">
                    {novelChapters.length === 0 ? <EmptyState title="No chapters" /> : novelChapters.map((chapter) => (
                      <ChapterCard
                        key={chapter.chapter_id}
                        chapter={chapter}
                        selected={chapter.chapter_id === selectedChapterId}
                        onSelect={() => {
                          setSelectedChapterId(chapter.chapter_id);
                          setChapterDraftText(chapter.draft_text ?? "");
                          setChapterDraftSavedText(chapter.draft_text ?? "");
                          void fetchNovelDraftSnapshots(selectedProjectId, chapter.chapter_id).then((snapshots) => setNovelSnapshots(snapshots.snapshots));
                        }}
                      />
                    ))}
                  </div>
                </div>
                <ChapterEditorPro>
                  <NovelToolbar
                    title="Chapter Editor Pro"
                    meta={selectedChapter ? <><span className="muted">{selectedChapter.title}</span> <WordCountBadge text={chapterDraftText} /> <DraftSaveStatus dirty={chapterDraftText !== chapterDraftSavedText} /></> : <span className="muted">Select a chapter</span>}
                    actions={<><button type="button" disabled={!selectedChapter} onClick={handleSaveChapterDraft}>Save Draft</button><button type="button" disabled={!selectedChapter} onClick={handleCreateScene}>Add Scene</button><button type="button" disabled={!selectedChapter} onClick={handleCreateSnapshot}>Create Snapshot</button></>}
                  />
                  {selectedChapter ? (
              <div className="stack">
                <textarea value={chapterDraftText} onChange={(event) => setChapterDraftText(event.target.value)} rows={8} />
                <LinkedRefList title="Linked scenes" refs={selectedChapter.scene_refs ?? []} />
                <LinkedRefList title="Linked characters" refs={selectedChapter.linked_character_ids ?? []} />
                <LinkedRefList title="Linked timeline events" refs={selectedChapter.linked_timeline_event_ids ?? []} />
                <DraftVersionPanel snapshots={novelSnapshots} onCompare={(snapshotId) => void handleCompareSnapshot(snapshotId)} />
              </div>
            ) : (
              <EmptyState title="Select a chapter." />
            )}
                </ChapterEditorPro>
              </div>
              <SceneCardsBoard scenes={novelScenes.filter((scene) => !selectedChapterId || scene.chapter_id === selectedChapterId)} />
              <div className="mode-landing-grid">
                <NovelSafeSummaryPanel title="Structure Tools">
                  <p>Outline editor, character arcs, plot threads, foreshadowing, timeline links, and quality checks remain local Novel drafts.</p>
                </NovelSafeSummaryPanel>
                <OutlineTreePro
                  chapters={novelChapters}
                  scenes={novelScenes}
                  selectedChapterId={selectedChapterId}
                  onSelectChapter={(chapterId) => {
                    const chapter = novelChapters.find((item) => item.chapter_id === chapterId);
                    setSelectedChapterId(chapterId);
                    setChapterDraftText(chapter?.draft_text ?? "");
                    setChapterDraftSavedText(chapter?.draft_text ?? "");
                    void fetchNovelDraftSnapshots(selectedProjectId, chapterId).then((snapshots) => setNovelSnapshots(snapshots.snapshots));
                  }}
                />
                <CharacterArcPanel chapters={novelChapters} scenes={novelScenes} />
                <PlotForeshadowingBoard chapters={novelChapters} scenes={novelScenes} />
                <TimelineLinkPanel chapters={novelChapters} scenes={novelScenes} />
                <WorldBibleSidebar chapters={novelChapters} scenes={novelScenes} />
              </div>
              <div className="mode-landing-grid">
                <NovelPromptProviderPanel promptProfileId={selectedChapter?.prompt_profile_id ?? novelPreferences?.default_prompt_profile_id} providerSummary="Provider Gateway safe route; no API key shown." />
                <NovelExportWizard onExportMarkdown={() => void handleExport("markdown")} onExportTxt={() => void handleExport("txt")} />
                <NovelQualityDashboard issues={novelQualityIssues} />
                <WorldToNovelImportPanel preview={worldToNovelPreview} />
                <WritingSessionDashboard session={writingSession} currentWordCount={chapterCurrentWordCount} />
                <NovelSafeSummaryPanel title="Novel Local Preferences">
                  <p>Default export: {novelPreferences?.default_export_format ?? "markdown"}. Preferences are local and contain no secrets.</p>
                </NovelSafeSummaryPanel>
                <NovelSafeSummaryPanel title="Novel Recovery / Unsaved Draft UX">
                  <p>Unsaved draft state is visible. Recovery drafts exclude provider prompts, hidden context, debug memory, and API keys.</p>
                </NovelSafeSummaryPanel>
                <OutlineNodeView node={{ node_id: "sample", node_type: "beat", title: "Safe outline node", summary: "Local outline nodes never become World facts automatically.", status: "draft" }} />
              </div>
            </div>
          )}
          context={(
            <div className="stack">
              <NovelSafeSummaryPanel title="Safe Context Sidebar">
                <p>World Bible, character, timeline, quality, and prompt context tabs show safe summaries only.</p>
              </NovelSafeSummaryPanel>
              <LinkedRefList title="Cross-mode drafts" refs={crossModeDrafts.map((draft) => draft.artifact_id)} />
              <LinkedRefList title="World to Novel source events" refs={worldToNovelPreview ? ((worldToNovelPreview.source_event_ids as string[] | undefined) ?? []) : []} />
            </div>
          )}
          status={(
            <div className="button-row">
              <span>local-only</span>
              <span>save status: {chapterDraftText !== chapterDraftSavedText ? "unsaved draft" : "saved locally"}</span>
              <span>provider status: Provider Gateway safe route</span>
              <span>Novel draft / authoring mode</span>
              <span>{writingSession && !writingSession.ended_at ? `session words ${writingSession.word_count_current - writingSession.word_count_start}` : "no active writing session"}</span>
              <span>Novel UI does not directly modify GameState</span>
            </div>
          )}
        />
      </section>
      <section className="tool-card">
        <h3>Tavern Studio UI Pro</h3>
        <p className="muted">Tavern data is local RP material: sessions, messages, memory, and proposals. It never writes World GameState, EventLog, raw env, API keys, hidden facts, or raw state_deltas.</p>
        <ErrorPanel message={tavernError} compact />
        <SuccessPanel message={tavernMessage} compact />
        <TavernWorkspaceShell
          navigation={(
            <div className="stack">
              <TavernToolbar title="Characters / Sessions" meta={<p className="muted">Local RP workspace navigation: Characters, Sessions, Multi-NPC Scenes, Memory, Voice, Boundaries, Safety, Export, Cross-Mode.</p>} />
              <CharacterCardLibrary characters={tavernCharacters} selectedCharacterId={selectedTavernCharacterId} onSelect={setSelectedTavernCharacterId} />
              <div className="stack">
                {tavernSessions.map((session) => (
                  <TavernSessionCard
                    key={session.session_id}
                    session={session}
                    selected={session.session_id === selectedTavernSessionId}
                    onSelect={async () => {
                      setSelectedTavernSessionId(session.session_id);
                      try {
                        const messages = await fetchTavernMessages(selectedProjectId, session.session_id);
                        setTavernMessages(messages.messages);
                      } catch (err) {
                        setTavernError(toErrorMessage(err));
                      }
                    }}
                  />
                ))}
              </div>
            </div>
          )}
          main={(
            <div className="stack">
              <SingleCharacterChatPro
                session={tavernSessions.find((session) => session.session_id === selectedTavernSessionId) ?? null}
                character={tavernCharacters.find((character) => character.tavern_character_id === selectedTavernCharacterId) ?? null}
                messages={tavernMessages}
                input={chatInput}
                providerStatus="Provider Gateway safe route; API key not shown"
                memoryHints={tavernRecoveryRecords.slice(0, 3).map((record) => record.safe_draft_text)}
                safetyNotes={chatSafetyNotes}
                onInputChange={setChatInput}
                onSend={handleSendTavernMessage}
                onRecoveryDraft={handleCreateTavernRecoveryDraft}
              />
              <MultiNPCScenePro scenes={multiNPCScenes} selectedSceneId={selectedMultiNPCSceneId} onSelect={setSelectedMultiNPCSceneId} onGenerateNext={handleGenerateMultiNPCReply} />
            </div>
          )}
          context={(
            <div className="stack">
              <TavernPromptProviderPanel promptProfileId={tavernPreferences?.default_prompt_profile_id} providerProfileId={tavernPreferences?.default_provider_profile_id} modelId="safe summary only" />
              <RPMemoryPanel sessions={tavernSessions} recoveryRecords={tavernRecoveryRecords} matureVisible={Boolean(tavernPreferences?.mature_module_visible)} />
              <EmotionArcPanel messages={tavernMessages} />
              <RelationshipTonePanel characters={tavernCharacters} sessions={tavernSessions} onPropose={() => void handleBuildTavernApplyPlan()} />
              <SceneMoodPresetPanel presets={tavernScenePresets} selectedPresetId={tavernPreferences?.default_scene_mood_preset_id ?? ""} onSelect={setNewScenePresetId} onCreate={handleCreateScenePreset} />
              <CharacterVoiceLabPanel character={tavernCharacters.find((character) => character.tavern_character_id === selectedTavernCharacterId) ?? null} />
              <BoundaryMatureSettingsPanel preferences={tavernPreferences} />
              <RPSafetyDashboardPanel report={rpSafetyDashboard} onRun={handleRunRPSafety} />
              <TavernCrossModeSafetyPanel worldNpcs={worldNpcSummaries} exportPreview={tavernExportPreview} />
            </div>
          )}
          status={(
            <div className="button-row">
              <span>local-only</span>
              <span>provider safe summary; API key not shown</span>
              <span>Mature Module is disabled by default</span>
              <span>Tavern UI does not modify World GameState</span>
            </div>
          )}
        />
        <div className="mode-landing-grid">
          <TavernSafeSummaryPanel title="Character Card Library">
            <p>Local character cards can be imported as drafts. Embedded scripts are not executed and remote character downloads are not offered.</p>
          </TavernSafeSummaryPanel>
          <TavernCharacterEditor character={tavernCharacters.find((character) => character.tavern_character_id === selectedTavernCharacterId) ?? null} />
          <TavernSafeSummaryPanel title="World NPC to Tavern Character UX Pro">
            <p>Player-safe mode excludes NPC secrets and unknown facts. Apply to Tavern creates a Tavern draft only.</p>
            <div className="form-grid">
              <select value={selectedWorldNpcId} onChange={(event) => setSelectedWorldNpcId(event.target.value)}>
                <option value="">Select safe world NPC</option>
                {worldNpcSummaries.map((npc) => <option key={npc.npc_id} value={npc.npc_id}>{npc.display_name}</option>)}
              </select>
              <select value={worldNpcMode} onChange={(event) => setWorldNpcMode(event.target.value as "player_safe" | "authoring")}>
                <option value="player_safe">player_safe</option>
                <option value="authoring">authoring-only</option>
              </select>
              <button type="button" disabled={!selectedWorldNpcId} onClick={() => void handleAdaptWorldNpc(false)}>Preview</button>
              <button type="button" disabled={!selectedWorldNpcId} onClick={() => void handleAdaptWorldNpc(true)}>Apply to Tavern Draft</button>
            </div>
            {worldNpcAdapterPreview && <pre className="safe-json-preview">{JSON.stringify(worldNpcAdapterPreview, null, 2)}</pre>}
          </TavernSafeSummaryPanel>
          <TavernSafeSummaryPanel title="RP Safety Dashboard">
            <p>Overall status: {rpSafetyDashboard?.overall_status ?? "not_run"}. Safe issue rows only; hidden/mature/private text is not printed.</p>
            <button type="button" disabled={!selectedProjectId} onClick={handleRunRPSafety}>Run RP Safety Eval</button>
          </TavernSafeSummaryPanel>
          <TavernSafeSummaryPanel title="Tavern Session Export / Backup UX">
            <p>JSON safe export and Markdown transcript preview exclude API keys, hidden facts, NPC secrets, mature/private memory, debug data, raw prompts, and raw state_deltas.</p>
            <div className="button-row">
              <button type="button" disabled={!selectedProjectId} onClick={handlePreviewTavernExport}>Preview Export</button>
              <button type="button" disabled={!selectedProjectId} onClick={handleCreateTavernExport}>Confirm Export</button>
            </div>
            {tavernExportPreview && <p className="muted">{tavernExportPreview.session_count} session(s), {tavernExportPreview.message_count} safe message(s). {tavernExportPreview.filtering_policy.join("; ")}</p>}
          </TavernSafeSummaryPanel>
          <TavernSafeSummaryPanel title="Tavern Local Preferences">
            <p>Default character/session, panel visibility, prompt/provider profile IDs, and scene mood are saved locally. Mature module visible is default off.</p>
            <button type="button" disabled={!selectedProjectId} onClick={handleSaveTavernPreferences}>Save Tavern Preferences</button>
          </TavernSafeSummaryPanel>
          <TavernSafeSummaryPanel title="Tavern Recovery / Unsaved Session UX">
            <p>{tavernRecoveryRecords.length} safe recovery draft(s). Recovery drafts exclude prompt context, hidden facts, NPC secrets, mature/private content, debug memory, and API keys.</p>
          </TavernSafeSummaryPanel>
        </div>
        <div className="card-grid">
          <div>
            <h4>Characters</h4>
            <div className="form-grid">
              <input value={newTavernCharacterId} onChange={(event) => setNewTavernCharacterId(event.target.value)} />
              <input value={newTavernCharacterName} onChange={(event) => setNewTavernCharacterName(event.target.value)} />
              <button type="button" disabled={!selectedProjectId} onClick={handleCreateTavernCharacter}>Create Character</button>
            </div>
            <ItemList
              emptyText="No Tavern characters"
              items={tavernCharacters.map((character) => (
                <button
                  key={character.tavern_character_id}
                  type="button"
                  className={character.tavern_character_id === selectedTavernCharacterId ? "selected-list-button" : ""}
                  onClick={() => setSelectedTavernCharacterId(character.tavern_character_id)}
                >
                  {character.display_name}
                </button>
              ))}
            />
          </div>
          <div>
            <h4>Import Character Card</h4>
            <textarea value={tavernCardRaw} onChange={(event) => setTavernCardRaw(event.target.value)} rows={6} />
            <button type="button" disabled={!selectedProjectId} onClick={handleImportTavernCard}>Import Draft</button>
            <p className="muted">Creator notes and prompt-like fields are treated as untrusted authoring material.</p>
          </div>
          <div>
            <h4>Sessions</h4>
            <div className="form-grid">
              <input value={newTavernSessionId} onChange={(event) => setNewTavernSessionId(event.target.value)} />
              <input value={newTavernSessionTitle} onChange={(event) => setNewTavernSessionTitle(event.target.value)} />
              <button type="button" disabled={!selectedProjectId} onClick={handleCreateTavernSession}>Create Session</button>
            </div>
            <ItemList
              emptyText="No Tavern sessions"
              items={tavernSessions.map((session) => (
                <button
                  key={session.session_id}
                  type="button"
                  className={session.session_id === selectedTavernSessionId ? "selected-list-button" : ""}
                  onClick={async () => {
                    setSelectedTavernSessionId(session.session_id);
                    try {
                      const messages = await fetchTavernMessages(selectedProjectId, session.session_id);
                      setTavernMessages(messages.messages);
                    } catch (err) {
                      setTavernError(toErrorMessage(err));
                    }
                  }}
                >
                  {session.title} · {session.status}
                </button>
              ))}
            />
          </div>
        </div>
        <div className="card-grid">
          <div>
            <h4>Single Character Chat</h4>
            <label>
              Character
              <select value={selectedTavernCharacterId} onChange={(event) => setSelectedTavernCharacterId(event.target.value)}>
                <option value="">Select character</option>
                {tavernCharacters.map((character) => (
                  <option key={character.tavern_character_id} value={character.tavern_character_id}>{character.display_name}</option>
                ))}
              </select>
            </label>
            <label>
              User message
              <textarea value={chatInput} onChange={(event) => setChatInput(event.target.value)} rows={4} />
            </label>
            <button type="button" disabled={!selectedTavernSessionId || !selectedTavernCharacterId || !chatInput.trim()} onClick={handleSendTavernMessage}>Send</button>
            {chatSafetyNotes.length > 0 && (
              <details>
                <summary>Safety notes</summary>
                <ItemList emptyText="No notes" items={chatSafetyNotes.map((note) => <span key={note}>{note}</span>)} />
              </details>
            )}
          </div>
          <div>
            <h4>Messages</h4>
            <ItemList
              emptyText="No messages"
              items={tavernMessages.map((message) => (
                <span key={message.message_id}><strong>{message.speaker_type}</strong>: {message.content}</span>
              ))}
            />
          </div>
          <div>
            <h4>Scene Mood Presets</h4>
            <div className="form-grid">
              <input value={newScenePresetId} onChange={(event) => setNewScenePresetId(event.target.value)} />
              <input value={newScenePresetName} onChange={(event) => setNewScenePresetName(event.target.value)} />
              <button type="button" disabled={!selectedProjectId} onClick={handleCreateScenePreset}>Create Preset</button>
            </div>
            <ItemList
              emptyText="No scene presets"
              items={tavernScenePresets.map((preset) => (
                <span key={preset.preset_id}>{preset.name} · {(preset.mood_tags ?? []).join(", ") || "style-only"}</span>
              ))}
            />
          </div>
          <div>
            <h4>Multi-NPC Scene Pro</h4>
            <p className="muted">Multi-character scenes store Tavern messages only. They do not modify World GameState, EventLog, hidden facts, NPC secrets, or provider secrets.</p>
            <div className="form-grid">
              <input value={newMultiNPCSceneId} onChange={(event) => setNewMultiNPCSceneId(event.target.value)} />
              <input value={newMultiNPCSceneTitle} onChange={(event) => setNewMultiNPCSceneTitle(event.target.value)} />
              <button type="button" disabled={!selectedProjectId || tavernCharacters.length < 2} onClick={handleCreateMultiNPCScene}>Create Scene</button>
            </div>
            <label>
              Scene
              <select value={selectedMultiNPCSceneId} onChange={(event) => setSelectedMultiNPCSceneId(event.target.value)}>
                <option value="">Select scene</option>
                {multiNPCScenes.map((scene) => (
                  <option key={scene.scene_id} value={scene.scene_id}>{scene.title}</option>
                ))}
              </select>
            </label>
            <button type="button" disabled={!selectedProjectId || !selectedMultiNPCSceneId} onClick={handleGenerateMultiNPCReply}>Generate Next Reply</button>
            <ItemList
              emptyText={tavernCharacters.length < 2 ? "Create at least two Tavern characters first." : "No multi-NPC scenes"}
              items={multiNPCScenes.map((scene) => (
                <span key={scene.scene_id}>
                  {scene.title} · participants {scene.participant_ids.length} · turn {scene.current_turn_index + 1}
                </span>
              ))}
            />
          </div>
        </div>
        <div className="card-grid">
          <ProjectModeCard title="Lorebook / World Info" message="Safe lore context filters hidden facts, unknown NPC facts, authoring notes, and debug data." />
          <ProjectModeCard title="Relationship Tone" message="Relationship tone affects expression only; World relationship changes require proposal and validation." />
          <ProjectModeCard title="Multi-Character Scene" message="Multi-NPC Scene Pro uses safe per-speaker context and writes Tavern messages only." />
        </div>
      </section>
      <section className="tool-card">
        <h3>Cross-Mode Bridge</h3>
        <p className="muted">Cross-mode artifacts are drafts, proposals, reviews, validation reports, or audit records. Apply to World requires backend validation and explicit confirmation.</p>
        <CrossModeDashboardPanel
          drafts={crossModeDrafts}
          timeline={crossModeTimeline}
          links={crossModeLinks}
          conflicts={crossModeConflicts}
          audit={crossModeAudit}
        />
        <ErrorPanel message={crossModeError} compact />
        <SuccessPanel message={crossModeMessage} compact />
        <div className="card-grid">
          <div>
            <h4>Novel → World Review</h4>
            <label>
              Source ref
              <input value={crossModeSourceRef} onChange={(event) => setCrossModeSourceRef(event.target.value)} />
            </label>
            <label>
              Draft type
              <select value={crossModeDraftType} onChange={(event) => setCrossModeDraftType(event.target.value)}>
                <option value="npc_draft">NPC</option>
                <option value="location_draft">Location</option>
                <option value="quest_draft">Quest</option>
                <option value="fact_draft">Fact</option>
                <option value="item_draft">Item</option>
                <option value="faction_draft">Faction</option>
                <option value="timeline_event_draft">Timeline Event</option>
              </select>
            </label>
            <button type="button" disabled={!selectedProjectId} onClick={handleCreateCrossModeDraft}>Generate Draft</button>
            <p className="muted">Review only. This does not write content packs or GameState.</p>
          </div>
          <div>
            <h4>World → Novel</h4>
            <button type="button" disabled={!selectedProjectId} onClick={handlePreviewWorldToNovel}>Preview Chapter Draft</button>
            {worldToNovelPreview && (
              <div className="safe-preview-list">
                <p><strong>Suggested title:</strong> {String(worldToNovelPreview.suggested_title ?? "Draft preview")}</p>
                <p><strong>Excluded hidden/debug events:</strong> {String(worldToNovelPreview.hidden_events_excluded_count ?? 0)}</p>
                <p><strong>Source events:</strong> {((worldToNovelPreview.source_event_ids as string[] | undefined) ?? []).join(", ") || "none"}</p>
                <p className="muted">Preview is safe-summary only and does not modify World EventLog or GameState.</p>
              </div>
            )}
            <p className="muted">Preview excludes raw state_deltas and hidden/debug events.</p>
          </div>
          <div>
            <h4>Tavern → World Apply Review</h4>
            <label>
              Proposal id
              <input value={tavernProposalId} onChange={(event) => setTavernProposalId(event.target.value)} />
            </label>
            <button type="button" disabled={!selectedProjectId || !tavernProposalId.trim()} onClick={handleBuildTavernApplyPlan}>Build Apply Plan</button>
            <p className="muted">Apply plans require explicit confirmation; the UI does not mutate World state directly.</p>
          </div>
        </div>
        <div className="card-grid">
          <div>
            <h4>Drafts</h4>
            <ItemList
              emptyText="No cross-mode drafts"
              items={crossModeDrafts.map((draft) => (
                <div key={draft.artifact_id} className="stack" data-cross-mode-ref={`cross_mode:draft:${draft.artifact_id}`}>
                  <span>{draft.artifact_type} · {draft.validation_status ?? draft.status}</span>
                  <small>{draft.source_refs.join(", ") || "no source"} → {draft.target_refs.join(", ") || "no target"}</small>
                  <button type="button" onClick={() => void handleValidateCrossModeDraft(draft.artifact_id)}>Validate</button>
                </div>
              ))}
            />
          </div>
          <div>
            <h4>Timeline</h4>
            <ItemList
              emptyText="No timeline entries"
              items={crossModeTimeline.map((entry) => (
                <span key={entry.entry_id} data-cross-mode-ref={entry.source_ref}>{entry.source_mode}: {entry.title} · {entry.visibility}</span>
              ))}
            />
          </div>
          <div>
            <h4>Links</h4>
            {crossModeLinks ? (
              <ItemList
                emptyText="No link issues"
                items={[
                  <span key="broken">Broken: {crossModeLinks.broken_links.length}</span>,
                  <span key="hidden">Hidden risk: {crossModeLinks.hidden_target_risks.length}</span>,
                  <span key="duplicate">Duplicate: {crossModeLinks.duplicate_links.length}</span>
                ]}
              />
            ) : (
              <EmptyState title="No link review loaded." />
            )}
          </div>
          <div>
            <h4>Conflicts</h4>
            <ItemList
              emptyText="No conflicts"
              items={(crossModeConflicts?.conflicts ?? []).map((conflict) => (
                <span key={conflict.conflict_id}>{conflict.severity}: {conflict.conflict_type}</span>
              ))}
            />
          </div>
          <div>
            <h4>Audit</h4>
            <ItemList
              emptyText="No audit records"
              items={crossModeAudit.slice(-5).map((record) => (
                <span key={record.audit_id}>{record.action_type} · {record.result}</span>
              ))}
            />
          </div>
          <div>
            <h4>Validation</h4>
            <button type="button" disabled={!selectedProjectId} onClick={handleValidateCrossMode}>Run Cross-Mode Validation</button>
            <button type="button" disabled={!selectedProjectId} onClick={() => void loadCrossModeData()}>Refresh Bridge</button>
            <p className="muted">Normal reports do not show hidden facts, NPC secrets, debug memory, raw env, API keys, or raw state_deltas.</p>
          </div>
        </div>
      </section>
      <section className="tool-card">
        <h3>Script / Mod Platform Pro</h3>
        <p className="muted">Local-only Module Browser. No online marketplace, no package download, and no arbitrary code execution.</p>
        <ScriptModEntryPanel
          modules={modules}
          moduleDetail={moduleDetail}
          compatibilityMatrix={moduleMatrix}
          moduleQualityGate={moduleQualityGate}
          auditRecords={moduleAudit}
        />
        <ErrorPanel message={moduleError} compact />
        <SuccessPanel message={moduleMessage} compact />
        <div className="button-row">
          <button type="button" disabled={!selectedProjectId} onClick={handleScanModules}>Scan Local Modules</button>
          <button type="button" disabled={!selectedProjectId} onClick={() => void loadModuleData()}>Refresh</button>
          <button type="button" disabled={!selectedModuleId} onClick={handleValidateModule}>Validate</button>
          <button type="button" disabled={!selectedModuleId} onClick={handleCertifyModule}>Certify</button>
          <button type="button" disabled={!selectedModuleId} onClick={handleModuleQualityGate}>Quality Gate</button>
        </div>
        <AuthoringWorkspaceShell
          title="Authoring / Mod Workspace Layout Pro"
          status="dirty state: local UI only · validation status: review · package status: local-only"
          sidebar={
            <div className="stack">
              <SafeSummaryCard title="Validation" value={moduleDetail?.summary.validation_status ?? "not loaded"} detail="Safe summary only." />
              <SafeSummaryCard title="Permissions" value={modulePermissions?.risk_level ?? "not loaded"} detail="Dangerous permissions are default blocked." />
              <SafeSummaryCard title="Quality" value={moduleQualityGate ? (moduleQualityGate.ok ? "passed" : "blocked") : "not run"} detail="No auto-fix or package execution." />
            </div>
          }
        >
          <ModuleBrowserProPanel
            modules={modules}
            selectedModuleId={selectedModuleId}
            moduleSearchQuery={moduleSearchQuery}
            moduleTypeFilter={moduleTypeFilter}
            moduleRiskFilter={moduleRiskFilter}
            moduleValidationFilter={moduleValidationFilter}
            moduleCertificationFilter={moduleCertificationFilter}
            moduleCertificationLevel={moduleCertificationLevel}
            moduleQualityGate={moduleQualityGate}
            onSearchChange={setModuleSearchQuery}
            onTypeFilterChange={setModuleTypeFilter}
            onRiskFilterChange={setModuleRiskFilter}
            onValidationFilterChange={setModuleValidationFilter}
            onCertificationFilterChange={setModuleCertificationFilter}
            onSelectModule={(packageId) => void handleSelectModule(packageId)}
          />
          <div className="card-grid">
            <div>
              <h4>Module Detail</h4>
              {moduleDetail ? (
                <div className="stack">
                  <p><strong>{moduleDetail.summary.name}</strong> {moduleDetail.summary.version}</p>
                  <p className="muted">{moduleDetail.summary.package_id} · {moduleDetail.summary.safe_path_hint}</p>
                  <p>Validation: {moduleDetail.summary.validation_status}</p>
                  <p>Compatibility: {moduleDetail.summary.compatibility_status}</p>
                  <p>Targets: {moduleDetail.target_project_modes.join(", ") || "not specified"}</p>
                  <p>Dependencies: {moduleDetail.dependencies.join(", ") || "none"}</p>
                  <p>Conflicts: {moduleDetail.conflicts.join(", ") || "none"}</p>
                  <ItemList emptyText="No errors." items={moduleDetail.summary.errors.map((item) => <span key={item} className="danger-text">{redactReportText(item)}</span>)} />
                  <ItemList emptyText="No warnings." items={moduleDetail.summary.warnings.map((item) => <span key={item}>{redactReportText(item)}</span>)} />
                </div>
              ) : (
                <EmptyState title="Select a local module." detail="Scan the project modules directory to populate this panel." />
              )}
            </div>
            <ExtensionCertificationProPanel moduleCertificationLevel={moduleCertificationLevel} moduleQualityGate={moduleQualityGate} />
          </div>
          <ModPermissionDashboardProPanel
            modulePermissions={modulePermissions}
            permissionSummaries={modulePermissionSummaries}
            riskFilter={moduleRiskFilter}
            onRiskFilterChange={setModuleRiskFilter}
          />
          <CompatibilityMatrixProPanel matrix={moduleMatrix} selectedCompatibility={moduleCompatibility} />
          <ImportExportWizardProPanel />
          <ModQualityGateProPanel gate={moduleQualityGate} />
          <ModulePlaytestStressProPanel
            modules={modules}
            selectedModuleId={selectedModuleId}
            compatibilityMatrix={moduleMatrix}
            qualityGate={moduleQualityGate}
            error={moduleError}
            disabled={!selectedProjectId}
            onSelectModule={(packageId) => void handleSelectModule(packageId)}
            onRunSelectedPlaytest={() => void handleModulePlaytestGate()}
            onRunCompatibilityStress={() => void handleModuleCompatibilityStressSummary()}
            onRunQualityGate={handleModuleQualityGate}
          />
          <RuleModuleContractPanel />
          <AuthoringValidationDashboardPanel modules={modules} />
          <AuthoringDiffPreview validationStatus={moduleDetail?.summary.validation_status ?? "not_run"} destructive={Boolean(moduleCompatibility && String(moduleCompatibility.status ?? "") === "blocked")} />
          <AuthoringAuditTrailPanel
            moduleAudit={moduleAudit}
            crossModeAudit={crossModeAudit}
            riskFilter={auditRiskFilter}
            resultFilter={auditResultFilter}
            onRiskFilterChange={setAuditRiskFilter}
            onResultFilterChange={setAuditResultFilter}
            onJumpPackage={(packageId) => void handleSelectModule(packageId)}
          />
          <AuthoringBackupRestorePanel />
          <SafeApplyWorkflowPanel canApply={Boolean(moduleDetail && moduleDetail.summary.validation_status === "valid" && moduleQualityGate?.ok)} />
        </AuthoringWorkspaceShell>
        <details>
          <summary>All permissions</summary>
          <ItemList
            emptyText="No permission summaries."
            items={modulePermissionSummaries.map((item) => (
              <span key={item.package_id}>{item.package_id}: {item.risk_level} · {item.dangerous_permissions.join(", ") || "no dangerous permissions"}</span>
            ))}
          />
        </details>
        {moduleCompatibility && <p className="muted">Selected compatibility: {String(moduleCompatibility.status ?? "unknown")}</p>}
      </section>
    </div>
  );
}

function ProjectModeCard({ title, status, message }: { title: string; status?: NarrativeProjectModeStatus; message: string }) {
  return (
    <div className="tool-card">
      <h3>{title}</h3>
      <p className="muted">{message}</p>
      <StatusBadge label={status?.enabled ? "enabled" : "stub"} enabled={Boolean(status?.enabled)} />
      {status?.missing_requirements?.length ? (
        <ItemList emptyText="Configured" items={status.missing_requirements.map((item) => <span key={item}>{item}</span>)} />
      ) : (
        <p className="muted">Configured safely. No API keys, hidden facts, or raw env are shown here.</p>
      )}
    </div>
  );
}

function LocalOnlyNotice({ children }: { children: ReactNode }) {
  return (
    <div className="local-only-notice">
      <strong>Local only</strong>
      <p>{children}</p>
    </div>
  );
}

function SuccessPanel({ message, compact = false }: { message: string; compact?: boolean }) {
  if (!message) {
    return null;
  }
  return (
    <div className={`success-panel ${compact ? "compact" : ""}`} role="status">
      <strong>Done</strong>
      <p>{message}</p>
    </div>
  );
}

function StatusBadge({ label, enabled }: { label: string; enabled: boolean | undefined }) {
  const state = enabled ? "enabled" : "disabled";
  return <span className={`status-badge ${state}`}>{label}: {state}</span>;
}

function StatusDot({ label, enabled }: { label: string; enabled: boolean | undefined }) {
  return (
    <p><StatusBadge label={label} enabled={enabled} /></p>
  );
}

function SocialPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const factions = visibleState?.factions ?? [];
  const rumors = visibleState?.known_rumors ?? [];
  const crimes = visibleState?.known_crimes ?? [];
  const relationships = visibleState?.relationships ?? [];
  const conflicts = visibleState?.faction_conflicts ?? [];

  return (
    <div className="stack">
      <div>
        <h3>Known Factions</h3>
        <ItemList
          emptyText="None"
          items={factions.map((faction) => (
            <span key={faction.id}>
              {faction.name} <span className="badge">{faction.band}</span>
            </span>
          ))}
        />
      </div>
      <div>
        <h3>Known Rumors</h3>
        <ItemList
          emptyText="None"
          items={rumors.map((rumor) => (
            <span key={rumor.id}>{rumor.text_for_player}</span>
          ))}
        />
      </div>
      <div>
        <h3>Known Crimes</h3>
        <ItemList
          emptyText="None"
          items={crimes.map((crime) => (
            <span key={crime.id}>
              {crime.crime_type} <span className="badge">{crime.status}</span>
            </span>
          ))}
        />
      </div>
      <div>
        <h3>Known Relationships</h3>
        <ItemList
          emptyText="None"
          items={relationships.map((relationship) => (
            <span key={relationship.id}>
              {relationship.source_id} {relationship.relation_type} {relationship.target_id}
            </span>
          ))}
        />
      </div>
      <div>
        <h3>Faction Conflicts</h3>
        <ItemList
          emptyText="None"
          items={conflicts.map((conflict) => (
            <span key={conflict.faction_id}>
              {conflict.faction_id} alert {conflict.alert_level}
            </span>
          ))}
        />
      </div>
    </div>
  );
}

function SaveBrowser({
  saves,
  selectedSaveId,
  migrationStatusBySaveId,
  migrationResultBySaveId,
  migrationError,
  saveWorldFilter,
  isLoading,
  onSave,
  onLoad,
  onDelete,
  onRefresh,
  onCheckMigration,
  onDryRunMigration,
  onApplyMigration,
  onExportSave,
  onSelectSave,
  onFilterWorld
}: {
  saves: SaveSummary[];
  selectedSaveId: string;
  migrationStatusBySaveId: Record<string, SaveMigrationStatus>;
  migrationResultBySaveId: Record<string, SaveMigrationResponse>;
  migrationError: string;
  saveWorldFilter: string;
  isLoading: boolean;
  onSave: () => void;
  onLoad: () => void;
  onDelete: (saveId: string) => void;
  onRefresh: () => void;
  onCheckMigration: (saveId: string) => void;
  onDryRunMigration: (saveId: string) => void;
  onApplyMigration: (saveId: string) => void;
  onExportSave: (saveId: string) => void;
  onSelectSave: (saveId: string) => void;
  onFilterWorld: (worldId: string) => void;
}) {
  const worldOptions = Array.from(new Set(saves.map((save) => save.world_id))).sort();
  const selectedSave = saves.find((save) => save.save_id === selectedSaveId) ?? null;
  const selectedStatus = selectedSaveId ? migrationStatusBySaveId[selectedSaveId] : undefined;
  const selectedResult = selectedSaveId ? migrationResultBySaveId[selectedSaveId] : undefined;
  return (
    <section className="tool-section player-zone">
      <PageHeader
        eyebrow="Player saves"
        title="Save Browser"
        description="Local save/load and migration controls. Summaries omit hidden facts and raw GameState."
      />
      <div className="save-browser-actions">
        <button type="button" onClick={onSave} disabled={isLoading}>
          Save
        </button>
        <button type="button" onClick={onLoad} disabled={!selectedSaveId || isLoading}>
          Load
        </button>
        <button type="button" onClick={() => onDelete(selectedSaveId)} disabled={!selectedSaveId || isLoading}>
          Delete
        </button>
        <button type="button" onClick={onRefresh} disabled={isLoading}>
          Refresh
        </button>
        <button type="button" onClick={() => onExportSave(selectedSaveId)} disabled={!selectedSaveId || isLoading}>
          Export Bundle
        </button>
      </div>
      <p className="muted">
        Import uses the local authoring import API or CLI with a zip bundle. It never reads API
        keys, .env files, or raw hidden state from the player UI.
      </p>
      <label>
        World filter
        <select
          value={saveWorldFilter}
          onChange={(event) => onFilterWorld(event.target.value)}
          disabled={isLoading}
        >
          <option value="">All worlds</option>
          {worldOptions.map((worldId) => (
            <option key={worldId} value={worldId}>
              {worldId}
            </option>
          ))}
        </select>
      </label>
      <div className="save-list">
        {saves.length === 0 && <EmptyState title="No saves." detail="Create a local save before loading or migrating." />}
        {saves.map((save) => (
          <button
            type="button"
            className={`save-card ${selectedSaveId === save.save_id ? "selected" : ""}`}
            key={save.save_id}
            onClick={() => onSelectSave(save.save_id)}
          >
            <strong>{save.world_name || save.world_id}</strong>
            <span>{save.current_location_name}</span>
            <span>{save.formatted_time}</span>
            <span>Turn {save.turn}</span>
            <span className="muted">{save.updated_at}</span>
          </button>
        ))}
      </div>
      <MigrationPanel
        saves={saves}
        selectedSave={selectedSave}
        migrationStatusBySaveId={migrationStatusBySaveId}
        status={selectedStatus}
        result={selectedResult}
        error={migrationError}
        isLoading={isLoading}
        onCheck={onCheckMigration}
        onDryRun={onDryRunMigration}
        onApply={onApplyMigration}
      />
    </section>
  );
}

function MigrationPanel({
  saves,
  selectedSave,
  migrationStatusBySaveId,
  status,
  result,
  error,
  isLoading,
  onCheck,
  onDryRun,
  onApply
}: {
  saves: SaveSummary[];
  selectedSave: SaveSummary | null;
  migrationStatusBySaveId: Record<string, SaveMigrationStatus>;
  status: SaveMigrationStatus | undefined;
  result: SaveMigrationResponse | undefined;
  error: string;
  isLoading: boolean;
  onCheck: (saveId: string) => void;
  onDryRun: (saveId: string) => void;
  onApply: (saveId: string) => void;
}) {
  if (!selectedSave) {
    return (
      <div className="migration-panel">
        <h3>Save Migration Visualizer</h3>
        <EmptyState title="No save selected." detail="Select a save to inspect schema version, migration plan, dry-run result, module changes, and destructive-change blockers." />
      </div>
    );
  }
  const planRows = buildSaveMigrationPlanRows(selectedSave, status, result);
  const moduleRows = buildSaveModuleMigrationRows(selectedSave, status, result);
  const destructiveBlocked = buildDestructiveMigrationBlockers(status, result);

  return (
    <div className="migration-panel save-migration-visualizer">
      <h3>Save Migration Visualizer</h3>
      <p className="muted">Local read-only visualizer. Dry-run does not write data; apply requires explicit confirm and the backend migration flow. Raw save JSON, hidden facts, and API keys are not displayed.</p>
      <ErrorPanel message={error} compact />
      <div className="provider-table-wrap">
        <table className="provider-table">
          <thead>
            <tr>
              <th>Save</th>
              <th>World</th>
              <th>Schema version</th>
              <th>Migration needed</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {saves.map((save) => {
              const saveStatus = migrationStatusBySaveId[save.save_id];
              return (
                <tr key={save.save_id} className={save.save_id === selectedSave.save_id ? "selected-row" : ""}>
                  <td>{save.save_id}</td>
                  <td>{save.world_id}</td>
                  <td>{saveStatus?.schema_version ?? "not checked"}</td>
                  <td>{saveStatus ? (saveStatus.needs_migration ? "yes" : "no") : "check required"}</td>
                  <td>{save.updated_at}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <dl className="metadata-list">
        <dt>Save</dt>
        <dd>{selectedSave.save_id}</dd>
        <dt>World</dt>
        <dd>{status?.world_id ?? selectedSave.world_id}</dd>
        <dt>Engine</dt>
        <dd>{status?.engine_version ?? "Check required"}</dd>
        <dt>Schema</dt>
        <dd>{status?.schema_version ?? "Check required"}</dd>
        <dt>World version</dt>
        <dd>{status?.world_version ?? "Unknown"}</dd>
        <dt>Content pack</dt>
        <dd>{status?.content_pack_version ?? "Unknown"}</dd>
        <dt>Status</dt>
        <dd>
          <StatusBadge
            label={status ? (status.needs_migration ? "Migration needed" : "Current") : "Not checked"}
            enabled={status ? !status.needs_migration : false}
          />
        </dd>
        <dt>Last migrated</dt>
        <dd>{lastMigratedAt(result)}</dd>
      </dl>
      {status?.migration_path.length ? (
        <p className="muted">Path: {status.migration_path.join(" -> ")}</p>
      ) : (
        <p className="muted">Dry-run is safe and does not write the database.</p>
      )}
      <section>
        <h4>Migration plan</h4>
        <div className="safe-summary-grid">
          <SafeSummaryCard title="Steps" value={String(planRows.length)} detail="Schema migration steps from local status/dry-run summaries." />
          <SafeSummaryCard title="Affected fields" value={planRows.map((row) => row.affectedFields).join(", ") || "none"} detail="Field groups only; raw save JSON is hidden." />
          <SafeSummaryCard title="Module state changes" value={String(moduleRows.length)} detail="Module ids and schema-impact summaries only." />
          <SafeSummaryCard title="Destructive blocked" value={destructiveBlocked.length ? "blocked" : "not requested"} detail="Removal/destructive changes are not applied automatically." />
        </div>
        <ItemList
          emptyText="No migration steps loaded. Run Check or Dry-run."
          items={planRows.map((row) => (
            <span key={row.stepId}>
              {row.stepId}: {row.sourceVersion} {"->"} {row.targetVersion} · {row.affectedFields}
            </span>
          ))}
        />
      </section>
      <section>
        <h4>Module state migration</h4>
        <ItemList
          emptyText="No module state migration changes detected."
          items={moduleRows.map((row) => (
            <span key={row.moduleId}>
              {row.moduleId}: {row.changeSummary}
            </span>
          ))}
        />
      </section>
      {status?.warnings.length ? (
        <ul className="compact-list warning-list">
          {status.warnings.map((warning) => (
            <li key={warning}>{sanitizeDisplayError(warning)}</li>
          ))}
        </ul>
      ) : null}
      <div className="save-browser-actions">
        <button type="button" onClick={() => onCheck(selectedSave.save_id)} disabled={isLoading}>
          Check
        </button>
        <button type="button" onClick={() => onDryRun(selectedSave.save_id)} disabled={isLoading}>
          Dry-run
        </button>
        <button
          type="button"
          onClick={() => onApply(selectedSave.save_id)}
          disabled={isLoading || !status?.needs_migration}
        >
          Apply
        </button>
      </div>
      {result && (
        <div className="migration-result">
          <p>
            {result.dry_run ? "Dry-run" : "Apply"} {result.success ? "succeeded" : "failed"}:{" "}
            {result.source_version} {"->"} {result.target_version}
          </p>
          {result.backup_save_id && <p>Backup: {result.backup_save_id}</p>}
          {result.applied_migrations.length > 0 && (
            <details>
              <summary>Migration history</summary>
              <ul className="compact-list">
                {result.applied_migrations.map((entry) => (
                  <li key={`${entry.migration_id}-${entry.applied_at}`}>
                    {entry.migration_id}: {entry.source_version} {"->"} {entry.target_version} at{" "}
                    {entry.applied_at}
                  </li>
                ))}
              </ul>
            </details>
          )}
          <details>
            <summary>Warnings and destructive blockers</summary>
            <ItemList
              emptyText="No migration warnings or destructive blockers."
              items={[...result.warnings.map(sanitizeDisplayError), ...destructiveBlocked].map((warning, index) => (
                <span key={`${warning}-${index}`}>{warning}</span>
              ))}
            />
          </details>
        </div>
      )}
    </div>
  );
}

function buildSaveMigrationPlanRows(
  save: SaveSummary,
  status: SaveMigrationStatus | undefined,
  result: SaveMigrationResponse | undefined
): Array<{ stepId: string; sourceVersion: string; targetVersion: string; affectedFields: string }> {
  if (result?.applied_migrations.length) {
    return result.applied_migrations.map((entry) => ({
      stepId: entry.migration_id,
      sourceVersion: entry.source_version,
      targetVersion: entry.target_version,
      affectedFields: inferMigrationAffectedFields(entry.description)
    }));
  }
  if (status?.migration_path.length) {
    return status.migration_path.map((step, index) => ({
      stepId: step,
      sourceVersion: index === 0 ? status.schema_version : status.migration_path[index - 1] ?? status.schema_version,
      targetVersion: index === status.migration_path.length - 1 ? status.target_schema_version : status.migration_path[index + 1] ?? status.target_schema_version,
      affectedFields: inferMigrationAffectedFields(`${step} ${status.warnings.join(" ")}`)
    }));
  }
  return [{
    stepId: "current-schema-check",
    sourceVersion: status?.schema_version ?? "unknown",
    targetVersion: status?.target_schema_version ?? status?.schema_version ?? "unknown",
    affectedFields: save.enabled_mods && Object.keys(save.enabled_mods).length ? "schema metadata, module state summary" : "schema metadata"
  }];
}

function buildSaveModuleMigrationRows(
  save: SaveSummary,
  status: SaveMigrationStatus | undefined,
  result: SaveMigrationResponse | undefined
): Array<{ moduleId: string; changeSummary: string }> {
  const moduleIds = Object.keys(save.enabled_mods ?? {});
  const warningText = [...(status?.warnings ?? []), ...(result?.warnings ?? [])].join(" ");
  if (!moduleIds.length && !/module/i.test(warningText)) {
    return [];
  }
  if (!moduleIds.length) {
    return [{ moduleId: "module-state", changeSummary: "Module migration warning present; run dry-run for safe details." }];
  }
  return moduleIds.map((moduleId) => ({
    moduleId,
    changeSummary: /remove|delete|destructive/i.test(warningText)
      ? "Destructive module state change blocked by default."
      : "Preserve module state unless backend migration plan explicitly confirms a safe schema update."
  }));
}

function buildDestructiveMigrationBlockers(
  status: SaveMigrationStatus | undefined,
  result: SaveMigrationResponse | undefined
): string[] {
  const warnings = [...(status?.warnings ?? []), ...(result?.warnings ?? [])].map(sanitizeDisplayError);
  const blockers = warnings.filter((warning) => /destructive|remove|delete|drop|erase/i.test(warning));
  return blockers.length ? blockers : ["Destructive remove blocked by default; no module state is deleted without confirmed backend migration flow."];
}

function inferMigrationAffectedFields(description: string): string {
  const text = description.toLowerCase();
  const fields: string[] = [];
  if (/schema|version|engine/.test(text)) fields.push("schema version");
  if (/module|combat|economy|faction|magic|hacking|crafting|survival|cultivation/.test(text)) fields.push("module state");
  if (/event|timeline|delta/.test(text)) fields.push("EventLog metadata");
  if (/visibility|hidden|secret/.test(text)) fields.push("visibility metadata");
  if (/location|npc|quest|inventory/.test(text)) fields.push("visible state summary");
  return fields.length ? fields.join(", ") : "schema metadata";
}

function lastMigratedAt(result: SaveMigrationResponse | undefined): string {
  if (!result || result.applied_migrations.length === 0) {
    return "Not shown";
  }
  return result.applied_migrations[result.applied_migrations.length - 1]?.applied_at ?? "Not shown";
}

function StatusPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const visibleInjuries = (visibleState?.visible_npcs ?? []).filter(
    (npc) => npc.condition && npc.condition !== "healthy"
  );
  return (
    <div className="stack">
      <p className="muted">
        Player: {visibleState?.player_condition?.condition ?? "healthy"}
      </p>
      <div>
        <h3>Visible Injuries</h3>
        <ItemList
          emptyText="None"
          items={visibleInjuries.map((npc) => (
            <span key={npc.id}>
              {npc.id} <span className="badge">{npc.condition}</span>
            </span>
          ))}
        />
      </div>
      <div>
        <h3>Combat</h3>
        <p className="muted">
          {visibleState?.active_combat
            ? `${visibleState.active_combat.combat_id} (${visibleState.active_combat.status})`
            : "None"}
        </p>
      </div>
    </div>
  );
}

function DialogueModePanel({
  dialogue,
  groupScene,
  visibleState,
  configSummary,
  configError,
  isLoading,
  selectedMoodPresetId,
  onSelectMoodPreset,
  selectedDialogueMode,
  onSelectDialogueMode,
  onSelectPromptProfile,
  onStart,
  onEnd,
  onStartGroup,
  onNextGroupSpeaker,
  onEndGroup
}: {
  dialogue: DialogueModeResponse | null;
  groupScene: GroupDialogueSceneResponse | null;
  visibleState: VisibleState | null;
  configSummary: StudioConfigSummary | null;
  configError: string;
  isLoading: boolean;
  selectedMoodPresetId: string;
  onSelectMoodPreset: (presetId: string) => void;
  selectedDialogueMode: string;
  onSelectDialogueMode: (mode: string) => void;
  onSelectPromptProfile: (profileId: string) => void;
  onStart: (npcId: string, dialogueMode: string) => void;
  onEnd: () => void;
  onStartGroup: (npcIds: string[], sceneTopic: string, sceneMood: string) => void;
  onNextGroupSpeaker: () => void;
  onEndGroup: () => void;
}) {
  const activeDialogue = dialogue?.dialogue_session.status === "active" ? dialogue : null;
  const activeGroup = groupScene?.scene.status === "active" ? groupScene : null;
  const npcs = visibleState?.visible_npcs ?? [];
  const [selectedFocusNpcId, setSelectedFocusNpcId] = useState<string>("");
  const [selectedGroupNpcIds, setSelectedGroupNpcIds] = useState<string[]>([]);
  const [groupTopic, setGroupTopic] = useState<string>("local scene");
  const [groupMood, setGroupMood] = useState<string>("neutral");
  const selectedProfileId = configSummary?.selected_prompt_profile_id ?? "";
  const activeProfile = configSummary?.prompt_profiles.find((profile) => profile.id === selectedProfileId) ?? null;
  const focusNpcId = selectedFocusNpcId || npcs[0]?.id || "";
  const effectiveGroupIds = selectedGroupNpcIds.length > 0 ? selectedGroupNpcIds : npcs.slice(0, 2).map((npc) => npc.id);
  const toggleGroupNpc = (npcId: string) => {
    setSelectedGroupNpcIds((previous) => {
      const current = previous.length > 0 ? previous : npcs.slice(0, 2).map((npc) => npc.id);
      return current.includes(npcId) ? current.filter((id) => id !== npcId) : [...current, npcId];
    });
  };

  if (activeGroup) {
    return (
      <div className="dialogue-mode-panel">
        <div className="rp-panel-header">
          <div>
            <strong>Group RP scene</strong>
            <p className="muted">Local-only dialogue context. Debug and authoring data stay outside this panel.</p>
          </div>
          <span className="badge">{activeGroup.scene.scene_mood}</span>
        </div>
        <div className="rp-summary-grid">
          <p><span className="muted">Speaker</span>{activeGroup.scene.active_speaker_id || "none"}</p>
          <p><span className="muted">Topic</span>{activeGroup.scene.scene_topic || "open"}</p>
          <p><span className="muted">Mood preset</span>{activeGroup.scene.scene_mood_preset_id || "default"}</p>
          <p><span className="muted">Participants</span>{activeGroup.scene.participant_ids.length}</p>
        </div>
        <ItemList
          emptyText="No participant summaries."
          items={activeGroup.participant_contexts.map((context) => (
            <span className="rp-participant-row" key={context.npc_id}>
              <strong>{context.npc_id}</strong>
              <span>{context.emotional_summary || "neutral"}</span>
              <span>{context.relationship_tone_summary || "neutral tone"}</span>
              <span className="badge">safe summary</span>
            </span>
          ))}
        />
        <div className="button-list">
          <button type="button" onClick={onNextGroupSpeaker} disabled={isLoading}>
            Next speaker
          </button>
          <button type="button" onClick={onEndGroup} disabled={isLoading}>
            End group scene
          </button>
        </div>
      </div>
    );
  }
  if (activeDialogue) {
    return (
      <div className="dialogue-mode-panel">
        <div className="rp-panel-header">
          <div>
            <strong>{activeDialogue.dialogue_session.focus_npc_id}</strong>
            <p className="muted">Dialogue Mode uses visible facts, NPC knowledge, and safe RP memory only.</p>
          </div>
          <span className="badge">{activeDialogue.dialogue_session.dialogue_mode}</span>
        </div>
        <div className="rp-summary-grid">
          <p><span className="muted">Emotion</span>{activeDialogue.dialogue_context.emotional_summary || "neutral"}</p>
          <p><span className="muted">Tone</span>{activeDialogue.dialogue_context.relationship_tone_summary || "neutral"}</p>
          <p><span className="muted">Mood</span>{activeDialogue.dialogue_context.scene_mood_summary || activeDialogue.dialogue_session.scene_mood_preset_id || "default"}</p>
          <p><span className="muted">Safe memories</span>{activeDialogue.dialogue_context.rp_memory_summaries.length}</p>
        </div>
        {activeDialogue.dialogue_context.rp_prompt_style_summary && (
          <p className="muted">RP style: {activeDialogue.dialogue_context.rp_prompt_style_summary}</p>
        )}
        <p className="muted">
          Topics: {activeDialogue.dialogue_session.active_topics.length
            ? activeDialogue.dialogue_session.active_topics.join(", ")
            : "open"}
        </p>
        {!activeDialogue.output_ok && (
          <div className="notice rp-warning">
            <strong>Consistency warning</strong>
            <ItemList
              emptyText="No safe warning details."
              items={activeDialogue.output_issues.map((issue) => <span key={issue}>{issue}</span>)}
            />
          </div>
        )}
        <button type="button" onClick={onEnd} disabled={isLoading}>
          Exit dialogue
        </button>
      </div>
    );
  }
  if (npcs.length === 0) {
    return (
      <div className="dialogue-mode-panel">
        <p className="muted">No visible NPC is available for dialogue.</p>
        <p className="muted">RP controls will appear when a player-visible NPC is present.</p>
      </div>
    );
  }
  return (
    <div className="dialogue-mode-panel">
      <div className="rp-panel-header">
        <div>
          <strong>RP / Dialogue</strong>
          <p className="muted">Start constrained RP with player-visible NPCs. No hidden or debug fields are shown.</p>
        </div>
        <span className="badge">player safe</span>
      </div>
      <div className="rp-control-grid">
        <label>
          Focus NPC
          <select value={focusNpcId} onChange={(event) => setSelectedFocusNpcId(event.target.value)} disabled={isLoading}>
            {npcs.map((npc) => (
              <option key={npc.id} value={npc.id}>
                {npc.id}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dialogue mode
          <select value={selectedDialogueMode} onChange={(event) => onSelectDialogueMode(event.target.value)} disabled={isLoading}>
            {DIALOGUE_MODES.map((mode) => (
              <option key={mode} value={mode}>
                {mode}
              </option>
            ))}
          </select>
        </label>
        <label>
          Scene mood
          <select value={selectedMoodPresetId} onChange={(event) => onSelectMoodPreset(event.target.value)} disabled={isLoading}>
            {SCENE_MOOD_PRESETS.map((preset) => (
              <option key={preset.id || "default"} value={preset.id}>
                {preset.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          RP prompt profile
          <select
            value={selectedProfileId}
            onChange={(event) => onSelectPromptProfile(event.target.value)}
            disabled={isLoading || !configSummary}
          >
            {configSummary?.prompt_profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.name}
              </option>
            )) ?? <option value="">Unavailable</option>}
          </select>
        </label>
      </div>
      <div className="rp-safe-summary">
        <p><span className="muted">Active profile</span>{activeProfile?.rp_profile.name ?? (selectedProfileId || "default")}</p>
        <p><span className="muted">Provider boundary</span>{configSummary ? "safe summary only" : "config unavailable"}</p>
        {configError && <p className="compact-error">{configError}</p>}
      </div>
      <div className="button-list">
        <button type="button" onClick={() => onStart(focusNpcId, selectedDialogueMode)} disabled={isLoading || !focusNpcId}>
          Start dialogue
        </button>
      </div>
      {npcs.length >= 2 && (
        <div className="rp-group-controls">
          <label>
            Group topic
            <input value={groupTopic} onChange={(event) => setGroupTopic(event.target.value)} disabled={isLoading} />
          </label>
          <label>
            Group mood
            <input value={groupMood} onChange={(event) => setGroupMood(event.target.value)} disabled={isLoading} />
          </label>
          <div className="rp-checkbox-list">
            {npcs.map((npc) => (
              <label className="checkbox-field" key={npc.id}>
                <input
                  type="checkbox"
                  checked={effectiveGroupIds.includes(npc.id)}
                  onChange={() => toggleGroupNpc(npc.id)}
                  disabled={isLoading}
                />
                {npc.id}
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={() => onStartGroup(effectiveGroupIds, groupTopic, groupMood)}
            disabled={isLoading || effectiveGroupIds.length < 2}
          >
            Start group scene
          </button>
        </div>
      )}
    </div>
  );
}

function GraphPanel({
  title,
  graph,
  emptyText,
  showVisibility = false
}: {
  title: string;
  graph: GraphResponse | null;
  emptyText: string;
  showVisibility?: boolean;
}) {
  const safeGraph = showVisibility ? graph : graph ? filterPlayerGraph(graph) : null;
  if (!safeGraph || (safeGraph.nodes.length === 0 && safeGraph.edges.length === 0)) {
    return (
      <div className="graph-panel">
        <h3>{title}</h3>
        <p className="muted">{emptyText}</p>
      </div>
    );
  }

  return (
    <div className="graph-panel">
      <h3>{title}</h3>
      <MiniGraph graph={safeGraph} showVisibility={showVisibility} />
      <div className="graph-lists">
        <div>
          <h4>Nodes</h4>
          <ItemList
            emptyText="None"
            items={safeGraph.nodes.map((node) => (
              <span key={node.id}>
                {node.label} <span className="badge">{node.type}</span>
                {showVisibility && <span className="badge">{node.visibility}</span>}
              </span>
            ))}
          />
        </div>
        <div>
          <h4>Edges</h4>
          <ItemList
            emptyText="None"
            items={safeGraph.edges.map((edge, index) => (
              <span key={`${edge.source}-${edge.target}-${edge.type}-${index}`}>
                {edge.source} {"->"} {edge.target} <span className="badge">{edge.label ?? edge.type}</span>
                {edge.weight !== null && edge.weight !== undefined && (
                  <span className="badge">{edge.weight}</span>
                )}
                {showVisibility && <span className="badge">{edge.visibility}</span>}
              </span>
            ))}
          />
        </div>
      </div>
    </div>
  );
}

function MiniGraph({
  graph,
  showVisibility
}: {
  graph: GraphResponse;
  showVisibility: boolean;
}) {
  const nodes = graph.nodes.slice(0, 8);
  const positions = nodes.map((node, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(nodes.length, 1) - Math.PI / 2;
    return {
      node,
      x: 105 + Math.cos(angle) * 72,
      y: 82 + Math.sin(angle) * 56
    };
  });
  const positionById = new Map(positions.map((item) => [item.node.id, item]));
  const edges = graph.edges.filter(
    (edge) =>
      positionById.has(edge.source) &&
      positionById.has(edge.target) &&
      (showVisibility || edge.visibility === "player_visible")
  );

  return (
    <svg className="mini-graph" viewBox="0 0 210 164" role="img" aria-label={`${graph.scope} graph`}>
      {edges.map((edge, index) => {
        const source = positionById.get(edge.source);
        const target = positionById.get(edge.target);
        if (!source || !target) {
          return null;
        }
        return (
          <line
            key={`${edge.source}-${edge.target}-${index}`}
            x1={source.x}
            y1={source.y}
            x2={target.x}
            y2={target.y}
            className={edge.visibility === "debug_only" ? "debug-edge" : "player-edge"}
          />
        );
      })}
      {positions.map(({ node, x, y }) => (
        <g key={node.id}>
          <circle
            cx={x}
            cy={y}
            r={node.type === "player" ? 13 : 11}
            className={node.visibility === "debug_only" ? "debug-node" : "player-node"}
          />
          <text x={x} y={y + 24} textAnchor="middle">
            {shortLabel(node.label)}
          </text>
        </g>
      ))}
    </svg>
  );
}

function AuthoringToolNav({
  activeTool,
  onSelectTool
}: {
  activeTool: AuthoringToolId;
  onSelectTool: (toolId: AuthoringToolId) => void;
}) {
  return (
    <nav className="authoring-tool-nav" aria-label="Authoring tools">
      {AUTHORING_TOOL_NAV.map((tool) => (
        <button
          type="button"
          key={tool.id}
          className={activeTool === tool.id ? "active" : ""}
          onClick={() => onSelectTool(tool.id)}
        >
          <span>{tool.label}</span>
          <small>{tool.description}</small>
        </button>
      ))}
    </nav>
  );
}

function AuthoringWorkflowLauncher({ onLaunch }: { onLaunch: (toolId: AuthoringToolId) => void }) {
  const [presets, setPresets] = useState<AuthoringWorkflowPreset[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [activeStep, setActiveStep] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    void loadPresets();
  }, []);

  async function loadPresets() {
    setError("");
    try {
      const response = await fetchAuthoringWorkflowPresets();
      setPresets(response.presets);
      setSelectedId((current) => current || response.presets[0]?.id || "");
    } catch (err) {
      setPresets([]);
      setError(authoringErrorMessage(err));
    }
  }

  const selected = presets.find((preset) => preset.id === selectedId) ?? presets[0] ?? null;
  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Workflow Launcher</h2>
          <p className="muted">Open guided local workflows. Steps route to existing editors and validation gates.</p>
        </div>
        <button type="button" onClick={() => void loadPresets()}>Refresh Workflows</button>
      </div>
      {error && <ErrorPanel message={error} />}
      {selected ? (
        <>
          <div className="template-grid">
            <label>Preset<select value={selected.id} onChange={(event) => { setSelectedId(event.target.value); setActiveStep(""); }}>{presets.map((preset) => <option key={preset.id} value={preset.id}>{preset.name}</option>)}</select></label>
            <p className="muted">{selected.description}</p>
          </div>
          <div className="diff-summary">
            <h3>Steps</h3>
            {selected.steps.map((step) => (
              <p key={step.id}>
                <strong>{step.label}</strong> {step.action}
                <button type="button" onClick={() => { setActiveStep(step.id); onLaunch(workflowToolRefToAuthoringTool(step.tool_ref)); }}>Open</button>
                {activeStep === step.id && <span className="badge">active</span>}
              </p>
            ))}
          </div>
          <div className="diff-summary">
            <h3>Gates / Checks</h3>
            <p>Validation gates: {selected.validation_gates.join(", ") || "None"}</p>
            <p>Quality checks: {selected.quality_checks.join(", ") || "None"}</p>
            <p>Suggested templates: {selected.suggested_templates.join(", ") || "None"}</p>
          </div>
        </>
      ) : (
        <EmptyState title="No workflow presets." detail="Authoring workflow presets are local and read-only." />
      )}
    </section>
  );
}

function workflowToolRefToAuthoringTool(toolRef: string): AuthoringToolId {
  if (toolRef === "quality_gate") return "validation";
  if (toolRef === "import_export") return "diff_review";
  return AUTHORING_TOOL_NAV.some((tool) => tool.id === toolRef) ? (toolRef as AuthoringToolId) : "validation";
}

function AuthoringSection({
  toolId,
  activeTool,
  title,
  description,
  children
}: {
  toolId: AuthoringToolId;
  activeTool: AuthoringToolId;
  title: string;
  description: string;
  children: ReactNode;
}) {
  if (toolId !== activeTool) {
    return null;
  }
  return (
    <section className="authoring-section">
      <header className="authoring-section-header">
        <div>
          <h2>{title}</h2>
          <p className="muted">{description}</p>
        </div>
        <div className="authoring-section-badges">
          <span className="badge">authoring-only</span>
          <span className="badge">validated save</span>
        </div>
      </header>
      {children}
    </section>
  );
}

function DirtyStateBanner({ dirty, label }: { dirty: boolean; label: string }) {
  if (!dirty) {
    return null;
  }
  return (
    <div className="dirty-state-banner" role="status">
      <strong>Unsaved local edits</strong>
      <span>{label}</span>
    </div>
  );
}

function HiddenContentBadge({ visibility, hidden }: { visibility?: string | null; hidden?: boolean }) {
  const isHidden = hidden || visibility === "hidden";
  const isDiscoverable = visibility === "discoverable";
  if (!isHidden && !isDiscoverable) {
    return <span className="hidden-content-badge player-visible">player-visible</span>;
  }
  return (
    <span className={`hidden-content-badge ${isHidden ? "hidden" : "discoverable"}`}>
      {isHidden ? "hidden / authoring-only" : "discoverable"}
    </span>
  );
}

function AuthoringActionBar({
  onPreview,
  onValidate,
  onSave,
  disabled,
  previewLabel = "Preview",
  validateLabel = "Validate",
  saveLabel = "Save"
}: {
  onPreview: () => void;
  onValidate: () => void;
  onSave: () => void;
  disabled?: boolean;
  previewLabel?: string;
  validateLabel?: string;
  saveLabel?: string;
}) {
  return (
    <div className="authoring-action-bar">
      <button type="button" onClick={onPreview} disabled={disabled}>
        {previewLabel}
      </button>
      <button type="button" onClick={onValidate} disabled={disabled}>
        {validateLabel}
      </button>
      <button type="button" onClick={onSave} disabled={disabled}>
        {saveLabel}
      </button>
    </div>
  );
}

function PreviewResultPanel({
  title,
  validation,
  previewContent,
  onSelectIssue
}: {
  title: string;
  validation: AuthoringValidation | null;
  previewContent?: string;
  onSelectIssue?: (issue: AuthoringValidation["errors"][number]) => void;
}) {
  if (!validation && !previewContent) {
    return null;
  }
  return (
    <section className="preview-result-panel">
      <div className="authoring-pane-header compact">
        <div>
          <h3>{title}</h3>
          <p className={validation?.ok ? "validation-ok" : validation ? "error" : "muted"}>
            {validation
              ? validation.ok
                ? "No blocking errors."
                : `${validation.errors.length} blocking errors.`
              : "Preview generated."}
            {validation && validation.warnings.length > 0 ? ` ${validation.warnings.length} warnings.` : ""}
          </p>
        </div>
      </div>
      {validation && (
        <ValidationIssueList
          issues={[...validation.errors, ...validation.warnings, ...validation.suggestions]}
          onSelectIssue={onSelectIssue ?? (() => undefined)}
        />
      )}
      {previewContent && (
        <AuthoringOnlyPreviewDetails content={previewContent} />
      )}
    </section>
  );
}

function AuthoringOnlyPreviewDetails({
  content,
  title = "Authoring-only preview"
}: {
  content: string;
  title?: string;
}) {
  return (
    <details className="authoring-only-preview">
      <summary>{title} - hidden/private/debug fields are redacted</summary>
      <p className="muted">This preview is for local authoring review only. Player-safe previews must not include hidden facts, NPC secrets, private notes, debug data, raw prompts, raw state_deltas, or provider secrets.</p>
      <pre className="template-preview-code">{redactAuthoringPreviewText(content)}</pre>
    </details>
  );
}

function AuthoringPreviewCode({ content }: { content: string }) {
  return <pre className="template-preview-code">{redactAuthoringPreviewText(content)}</pre>;
}

function confirmDangerousAction(message: string): boolean {
  return window.confirm(message);
}

function ProjectSelectorPanel({
  workspaces,
  templates,
  currentWorkspaceId,
  pathValue,
  nameValue,
  error,
  message,
  onPathChange,
  onNameChange,
  onSelect,
  onAdd,
  onCreateFromTemplate
}: {
  workspaces: ProjectWorkspace[];
  templates: WorkspaceTemplate[];
  currentWorkspaceId: string;
  pathValue: string;
  nameValue: string;
  error: string;
  message: string;
  onPathChange: (value: string) => void;
  onNameChange: (value: string) => void;
  onSelect: (workspaceId: string) => void;
  onAdd: () => void;
  onCreateFromTemplate: (templateId: WorkspaceTemplateType, path: string, name?: string) => void;
}) {
  const currentWorkspace = workspaces.find((workspace) => workspace.workspace_id === currentWorkspaceId) ?? null;
  const [selectedTemplateId, setSelectedTemplateId] = useState<WorkspaceTemplateType>("blank_studio");
  const selectedTemplate = templates.find((template) => template.template_id === selectedTemplateId) ?? templates[0] ?? null;
  return (
    <section className="studio-section">
      <div className="section-heading-row">
        <div>
          <h3>Project Selector</h3>
          <p className="muted">Switch the local studio workspace reference without modifying active saves.</p>
        </div>
        <StatusBadge label={currentWorkspace?.safe_status ?? "no workspace"} enabled={currentWorkspace?.safe_status === "ok"} />
      </div>
      {workspaces.length === 0 ? (
        <EmptyState title="No workspace references." detail="Add a local workspace folder to start using the selector." />
      ) : (
        <div className="template-grid">
          <label>
            Current workspace
            <select value={currentWorkspaceId} onChange={(event) => onSelect(event.target.value)}>
              {workspaces.map((workspace) => (
                <option key={workspace.workspace_id} value={workspace.workspace_id}>
                  {workspace.name}
                </option>
              ))}
            </select>
          </label>
          {currentWorkspace && (
            <dl className="metadata-list">
              <dt>Path</dt>
              <dd><SafePathSummary value={currentWorkspace.path_redacted} /></dd>
              <dt>Project id</dt>
              <dd>{currentWorkspace.workspace_id}</dd>
              <dt>Mode status</dt>
              <dd>{currentWorkspace.safe_status}</dd>
              <dt>Worlds</dt>
              <dd>{currentWorkspace.world_count}</dd>
              <dt>Last opened</dt>
              <dd>{currentWorkspace.last_opened_at ?? "not opened yet"}</dd>
              <dt>Schema</dt>
              <dd>{currentWorkspace.schema_version}</dd>
            </dl>
          )}
        </div>
      )}
      <div className="template-grid">
        <label>
          Add local workspace path
          <input
            value={pathValue}
            onChange={(event) => onPathChange(event.target.value)}
            placeholder="D:\\KF\\world or another trusted local workspace"
          />
        </label>
        <label>
          Display name
          <input value={nameValue} onChange={(event) => onNameChange(event.target.value)} placeholder="Optional" />
        </label>
      </div>
      <div className="authoring-action-bar">
        <button type="button" onClick={onAdd} disabled={!pathValue.trim()}>
          Add Workspace
        </button>
      </div>
      <div className="template-preview">
        <div className="section-heading-row">
          <div>
            <h3>Create From Template</h3>
            <p className="muted">Create a local workspace skeleton. Templates never copy .env files or API keys.</p>
          </div>
        </div>
        <div className="template-grid">
          <label>
            Template
            <select
              value={selectedTemplate?.template_id ?? selectedTemplateId}
              onChange={(event) => setSelectedTemplateId(event.target.value as WorkspaceTemplateType)}
            >
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          {selectedTemplate && (
            <dl className="metadata-list">
              <dt>Description</dt>
              <dd>{selectedTemplate.description}</dd>
              <dt>Directories</dt>
              <dd>{selectedTemplate.directories.join(", ")}</dd>
              <dt>Starter world</dt>
              <dd>{selectedTemplate.starter_world ? "included" : "not included"}</dd>
              <dt>Workflows</dt>
              <dd>{selectedTemplate.recommended_workflow_presets.join(", ") || "none"}</dd>
            </dl>
          )}
        </div>
        <div className="authoring-action-bar">
          <button
            type="button"
            onClick={() => selectedTemplate && onCreateFromTemplate(selectedTemplate.template_id, pathValue, nameValue || selectedTemplate.name)}
            disabled={!selectedTemplate || !pathValue.trim()}
          >
            Create Workspace
          </button>
        </div>
      </div>
      <SuccessPanel message={message} compact />
      <ErrorPanel message={error} compact />
    </section>
  );
}

function RecentProjectsPanel({
  projects,
  onOpen,
  onRemove,
  onClear
}: {
  projects: RecentProjectEntry[];
  onOpen: (workspaceId: string) => void;
  onRemove: (workspaceId: string) => void;
  onClear: () => void;
}) {
  return (
    <section className="studio-section">
      <div className="section-heading-row">
        <div>
          <h3>Recent Projects</h3>
          <p className="muted">Reopen trusted local workspace references. Paths are redacted and only safe summaries are stored.</p>
        </div>
        <button type="button" onClick={onClear} disabled={projects.length === 0}>
          Clear
        </button>
      </div>
      {projects.length === 0 ? (
        <EmptyState title="No recent projects." detail="Select a workspace to add it to this local-only list." />
      ) : (
        <ul className="compact-list">
          {projects.map((project) => (
            <li key={project.workspace_id}>
              <strong>{project.display_name}</strong>
              <span className="muted"> - <SafePathSummary value={project.path_redacted} /></span>
              <span className="muted">
                {" "}
                - {project.last_world_id ? `last world ${project.last_world_id}` : "no world selected"}
              </span>
              <span className="muted"> - {project.last_opened_at}</span>
              <div className="authoring-action-bar">
                <button type="button" disabled title="Pinning is stored as local safe metadata when enabled by the backend.">
                  Pin
                </button>
                <button type="button" onClick={() => onOpen(project.workspace_id)}>
                  Open
                </button>
                <button type="button" onClick={() => onRemove(project.workspace_id)}>
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function LocalUpdateNotesPanel({
  index,
  error,
  onRefresh
}: {
  index: LocalUpdateNotesIndex | null;
  error: string;
  onRefresh: () => void;
}) {
  const notes = index?.release_notes ?? [];
  return (
    <section className="studio-section">
      <div className="section-heading-row">
        <div>
          <h3>Local Update Notes</h3>
          <p className="muted">Offline release notes from local docs. No network access or remote update checks.</p>
        </div>
        <div className="authoring-action-bar">
          <StatusBadge label={index?.current_version ?? "unknown"} enabled={Boolean(index)} />
          <button type="button" onClick={onRefresh}>Refresh</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      {index?.warnings.length ? (
        <div className="warning-list">
          {index.warnings.slice(0, 6).map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}
      {notes.length === 0 ? (
        <EmptyState title="No release notes found." detail="Add local docs/V*_RELEASE_NOTES.md files to populate this index." />
      ) : (
        <div className="template-grid">
          {notes.slice(0, 8).map((note) => (
            <article className="local-update-note-card" key={note.path}>
              <div className="section-heading-row">
                <div>
                  <h4>{note.version} - {note.title}</h4>
                  <p className="muted">{note.path}</p>
                </div>
              </div>
              <p>{note.summary}</p>
              {note.upgrade_notes.length > 0 && (
                <>
                  <h5>Upgrade Notes</h5>
                  <ul className="compact-list">
                    {note.upgrade_notes.slice(0, 3).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </>
              )}
              {note.known_limitations.length > 0 && (
                <>
                  <h5>Known Limitations</h5>
                  <ul className="compact-list">
                    {note.known_limitations.slice(0, 3).map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </>
              )}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function DesktopHealthCheckPanel({
  report,
  error,
  onRun,
  onOpenRecovery
}: {
  report: DesktopHealthCheckReport | null;
  error: string;
  onRun: () => void;
  onOpenRecovery: () => void;
}) {
  const checks = report?.checks ?? [];
  const blockers = checks.filter((check) => check.status === "error").length;
  const warnings = checks.filter((check) => check.status === "warning").length;
  return (
    <section className="studio-section desktop-health-panel">
      <div className="section-heading-row">
        <div>
          <h3>Desktop Health Check</h3>
          <p className="muted">Local diagnostics for backend, database, config, workspace, APIs, and provider setup.</p>
        </div>
        <div className="authoring-action-bar">
          <StatusBadge label={report?.overall_status ?? "not run"} enabled={report?.overall_status === "pass"} />
          <button type="button" onClick={onRun}>Run Check</button>
          <button type="button" onClick={onOpenRecovery}>Recovery</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
      <div className="studio-grid compact-dashboard-grid">
        <DashboardCard title="Overall" value={report?.overall_status ?? "none"}>
          <p>{report ? "Safe local report generated" : "Run a desktop health check"}</p>
        </DashboardCard>
        <DashboardCard title="Errors" value={String(blockers)}>
          <p>Blocking local issues</p>
        </DashboardCard>
        <DashboardCard title="Warnings" value={String(warnings)}>
          <p>Review recommended</p>
        </DashboardCard>
        <DashboardCard title="Workspace" value={report?.current_workspace?.safe_status ?? "none"}>
          <p>{report?.current_workspace?.path_redacted ?? "No selected workspace"}</p>
        </DashboardCard>
      </div>
      {checks.length === 0 ? (
        <EmptyState title="No health report yet." detail="Run the local health check to inspect desktop setup." />
      ) : (
        <div className="desktop-health-list">
          {checks.map((check) => (
            <article className={`desktop-health-item ${check.status}`} key={check.check_id}>
              <div className="section-heading-row">
                <strong>{check.label}</strong>
                <span className={`status-pill ${check.status}`}>{check.status}</span>
              </div>
              <p>{check.message}</p>
              {check.safe_detail && <p className="muted">{check.safe_detail}</p>}
            </article>
          ))}
        </div>
      )}
      <LocalOnlyNotice>
        Health reports do not include API keys, raw env, full sensitive paths, hidden facts, or raw prompts.
      </LocalOnlyNotice>
    </section>
  );
}

type ImportPackageKind = "world" | "mod" | "save";

function ImportPackagePanel() {
  const [kind, setKind] = useState<ImportPackageKind>("world");
  const [archiveBase64, setArchiveBase64] = useState<string>("");
  const [overwrite, setOverwrite] = useState<boolean>(false);
  const [importProfiles, setImportProfiles] = useState<ImportProfile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string>("safe");
  const [result, setResult] = useState<ArchiveImportResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const selectedProfile = importProfiles.find((profile) => profile.profile_id === selectedProfileId) ?? null;

  useEffect(() => {
    void loadProfiles();
  }, []);

  async function loadProfiles() {
    try {
      const catalog = await fetchImportExportProfiles();
      setImportProfiles(catalog.import_profiles);
      setSelectedProfileId((current) =>
        catalog.import_profiles.some((profile) => profile.profile_id === current)
          ? current
          : catalog.import_profiles[0]?.profile_id ?? "safe"
      );
    } catch {
      setImportProfiles([]);
      setSelectedProfileId("safe");
    }
  }

  async function handleImportApply() {
    const archive = archiveBase64.trim();
    if (!archive) {
      setError("Paste a local archive_base64 payload from an export response before importing.");
      return;
    }
    const confirmed = confirmDangerousAction(
      `${DANGEROUS_ACTION_COPY.importPackageApply}${overwrite ? " Overwrite is enabled." : ""}`
    );
    if (!confirmed) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response =
        kind === "world"
          ? await importWorldArchive(archive, overwrite, selectedProfileId)
          : kind === "mod"
            ? await importModArchive(archive, overwrite, selectedProfileId)
            : await importSaveArchive(archive, overwrite, selectedProfileId);
      setResult(response);
      setMessage(
        response.imported
          ? `${response.import_type} package imported after validation.`
          : `${response.import_type} package was not imported.`
      );
    } catch (err) {
      setResult(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard
      title="Import Package"
      description="Paste a local archive payload and apply it through the backend import validator."
      tone="authoring"
    >
      <div className="template-grid">
        <label>
          Package type
          <select value={kind} onChange={(event) => setKind(event.target.value as ImportPackageKind)} disabled={isBusy}>
            <option value="world">world</option>
            <option value="mod">mod</option>
            <option value="save">save bundle</option>
          </select>
        </label>
        <label>
          Import profile
          <select
            value={selectedProfileId}
            onChange={(event) => {
              const nextProfile = importProfiles.find((profile) => profile.profile_id === event.target.value);
              setSelectedProfileId(event.target.value);
              if (nextProfile && !nextProfile.allow_overwrite) {
                setOverwrite(false);
              }
            }}
            disabled={isBusy}
          >
            {importProfiles.length === 0 && <option value="safe">Safe Import</option>}
            {importProfiles.map((profile) => (
              <option key={profile.profile_id} value={profile.profile_id}>
                {profile.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          <input
            type="checkbox"
            checked={overwrite}
            onChange={(event) => setOverwrite(event.target.checked)}
            disabled={isBusy || selectedProfile?.allow_overwrite === false}
          />
          Allow overwrite
        </label>
      </div>
      {selectedProfile && (
        <p className="muted">
          Profile: validation {selectedProfile.require_validation ? "required" : "off"},
          quality gate {selectedProfile.require_quality_gate ? "required" : "off"},
          executables {selectedProfile.reject_executables ? "rejected" : "allowed"},
          hidden authoring data {selectedProfile.allow_hidden_authoring_data ? "reviewable" : "blocked"}.
        </p>
      )}
      <label className="full-width-field">
        archive_base64
        <textarea
          value={archiveBase64}
          onChange={(event) => {
            setArchiveBase64(event.target.value);
            setResult(null);
            setMessage("");
          }}
          placeholder="Paste archive_base64 from an export response. Do not paste API keys or .env contents."
          disabled={isBusy}
        />
      </label>
      <div className="authoring-action-bar">
        <button type="button" onClick={() => void handleImportApply()} disabled={isBusy || !archiveBase64.trim()}>
          Apply Import
        </button>
        <button
          type="button"
          onClick={() => {
            setArchiveBase64("");
            setResult(null);
            setMessage("Cleared import draft.");
          }}
          disabled={isBusy || !archiveBase64}
        >
          Clear
        </button>
      </div>
      {result && (
        <div className="authoring-preview-box">
          <p>
            <StatusBadge label={result.imported ? "Imported" : "Import blocked"} enabled={result.imported} />
          </p>
          <dl className="metadata-list">
            <dt>Type</dt>
            <dd>{result.import_type}</dd>
            <dt>Id</dt>
            <dd>{result.id}</dd>
            <dt>Validation</dt>
            <dd>{result.validation_ok ? "passed" : "failed"}</dd>
            <dt>Migration needed</dt>
            <dd>{result.migration_needed ? "yes" : "no"}</dd>
          </dl>
          <ItemList
            emptyText="No import warnings."
            items={[...result.errors, ...result.warnings, ...result.migration_warnings].map((item) => (
              <span key={item}>{sanitizeDisplayError(item)}</span>
            ))}
          />
        </div>
      )}
      <SuccessPanel message={message} compact />
      <ErrorPanel message={error} compact />
    </SectionCard>
  );
}

function AuthoringPanel({
  projectId,
  requestedTool,
  onRequestedToolHandled
}: {
  projectId: string;
  requestedTool: AuthoringToolId | null;
  onRequestedToolHandled: () => void;
}) {
  const [worlds, setWorlds] = useState<AuthoringWorldSummary[]>([]);
  const [selectedWorldId, setSelectedWorldId] = useState<string>("");
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("manifest.yaml");
  const [content, setContent] = useState<string>("");
  const [diskContent, setDiskContent] = useState<string>("");
  const [viewMode, setViewMode] = useState<AuthoringViewMode>("raw");
  const [activeAuthoringTool, setActiveAuthoringTool] = useState<AuthoringToolId>("project_dashboard");
  const [selectedEntityId, setSelectedEntityId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [preview, setPreview] = useState<AuthoringFilePreviewResponse | null>(null);
  const [selectedIssuePath, setSelectedIssuePath] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");

  useEffect(() => {
    void loadWorlds();
  }, []);

  useEffect(() => {
    if (selectedWorldId) {
      void loadFiles(selectedWorldId);
    }
  }, [selectedWorldId]);

  useEffect(() => {
    if (selectedWorldId && selectedFile) {
      void loadFile(selectedWorldId, selectedFile);
    }
  }, [selectedWorldId, selectedFile]);

  async function loadWorlds() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchAuthoringWorlds();
      setWorlds(response.worlds);
      setSelectedWorldId((current) => current || response.worlds[0]?.world_id || "");
    } catch (err) {
      setWorlds([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function loadFiles(worldId: string) {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchAuthoringFiles(worldId);
      setFiles(response.files);
      setSelectedFile((current) =>
        response.files.includes(current) ? current : response.files[0] ?? "manifest.yaml"
      );
      const detail = await fetchAuthoringWorld(worldId);
      setValidation(detail.validation);
    } catch (err) {
      setFiles([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function loadFile(worldId: string, fileName: string) {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchAuthoringFile(worldId, fileName);
      setContent(response.content);
      setDiskContent(response.content);
      setPreview(null);
      setSelectedEntityId("");
      setViewMode(FORM_SUPPORTED_FILES.has(fileName) ? "form" : "raw");
    } catch (err) {
      setContent("");
      setDiskContent("");
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    if (!selectedWorldId) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateAuthoringWorld(selectedWorldId);
      setValidation(response);
      setMessage(response.ok ? "Validation passed." : "Validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePreview() {
    if (!selectedWorldId || !selectedFile) {
      return null;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewAuthoringFileChange(selectedWorldId, selectedFile, content);
      setPreview(response);
      setValidation(response.validation_report);
      setMessage(
        response.validation_report.ok
          ? "Preview complete. Draft is valid."
          : "Preview found validation errors."
      );
      return response;
    } catch (err) {
      setError(authoringErrorMessage(err));
      return null;
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!selectedWorldId || !selectedFile) {
      return;
    }
    const previewResponse = await handlePreview();
    if (!previewResponse) {
      return;
    }
    if (!previewResponse.validation_report.ok) {
      setError("Validation errors block saving. Fix the draft before saving.");
      return;
    }
    if (
      (previewResponse.validation_report.warnings.length > 0 ||
        previewResponse.potential_save_migration_required) &&
      !confirmDangerousAction("Warnings or save-impact risks were found. Save this local file anyway?")
    ) {
      return;
    }
    const confirmed = confirmDangerousAction(DANGEROUS_ACTION_COPY.overwriteWorldFile);
    if (!confirmed) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await saveAuthoringFile(selectedWorldId, selectedFile, content);
      setValidation(response.validation);
      setPreview(null);
      setDiskContent(content);
      setMessage("Saved and validated.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleExportWorld() {
    if (!selectedWorldId || isBusy) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const exported = await exportWorldArchive(selectedWorldId);
      setMessage(
        `World archive ready: ${exported.file_name}. Import uses the local archive API/CLI and still runs validation.`
      );
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function handleSelectAuthoringTool(toolId: AuthoringToolId) {
    const preferredFile = AUTHORING_TOOL_NAV.find((tool) => tool.id === toolId)?.preferredFile;
    if (preferredFile && selectedFile !== preferredFile) {
      if (isDirty && !confirmDangerousAction("Discard unsaved local YAML edits and switch authoring tools?")) {
        return;
      }
      setSelectedFile(preferredFile);
    }
    setActiveAuthoringTool(toolId);
  }

  const usableFiles = files.length > 0 ? files : AUTHORING_FILES;
  const disabled = isBusy || worlds.length === 0;
  const isDirty = content !== diskContent;
  useEffect(() => {
    if (requestedTool) {
      handleSelectAuthoringTool(requestedTool);
      onRequestedToolHandled();
    }
  }, [requestedTool, onRequestedToolHandled]);
  const parsedEntities = useMemo(
    () => parseAuthoringEntities(selectedFile, content),
    [selectedFile, content]
  );
  const selectedEntity =
    parsedEntities.find((entity) => entity.id === selectedEntityId) ?? parsedEntities[0] ?? null;

  return (
    <section className="authoring-panel">
      <PageHeader
        eyebrow="Authoring"
        title="World Authoring"
        description="Local structured editor backed by the authoring API and validator."
        actions={
          <>
          {isDirty && <span className="dirty-badge">Unsaved changes</span>}
          <button type="button" onClick={() => void loadWorlds()} disabled={isBusy}>
            Refresh Worlds
          </button>
          <button type="button" onClick={() => void handleExportWorld()} disabled={!selectedWorldId || isBusy}>
            Export World
          </button>
          </>
        }
      />

      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice api-disabled-notice">
          Authoring API is disabled. Set <code>ENABLE_AUTHORING_API=true</code> on the backend to
          use the local editor.
        </div>
      )}
      <LocalOnlyNotice>
        Authoring edits write local content-pack files only after preview and validation. They never
        mutate an active game session. Import/export archives are zip bundles checked for path
        traversal, disallowed files, and validator errors before use.
      </LocalOnlyNotice>
      <ImportPackagePanel />

      <AuthoringWorkflowLauncher onLaunch={handleSelectAuthoringTool} />

      <AuthoringToolNav activeTool={activeAuthoringTool} onSelectTool={handleSelectAuthoringTool} />

      <div className="authoring-controls">
        <label>
          World
          <select
            value={selectedWorldId}
            onChange={(event) => setSelectedWorldId(event.target.value)}
            disabled={disabled}
          >
            {worlds.length === 0 && <option value="">Unavailable</option>}
            {worlds.map((world) => (
              <option key={world.world_id} value={world.world_id}>
                {world.name || world.world_id}
              </option>
            ))}
          </select>
        </label>

        <div className="segmented">
          <button
            type="button"
            className={viewMode === "form" ? "active" : ""}
            onClick={() => setViewMode("form")}
            disabled={!FORM_SUPPORTED_FILES.has(selectedFile)}
          >
            Form
          </button>
          <button
            type="button"
            className={viewMode === "raw" ? "active" : ""}
            onClick={() => setViewMode("raw")}
          >
            Raw YAML
          </button>
        </div>

        <AuthoringActionBar
          onPreview={() => void handlePreview()}
          onValidate={() => void handleValidate()}
          onSave={() => void handleSave()}
          disabled={!selectedWorldId || !selectedFile || isBusy}
        />
        <button
          type="button"
          onClick={() => {
            setContent(diskContent);
            setMessage("Discarded local edits.");
          }}
          disabled={!isDirty || isBusy}
        >
          Discard
        </button>
        <button
          type="button"
          onClick={() => selectedWorldId && selectedFile && void loadFile(selectedWorldId, selectedFile)}
          disabled={!selectedWorldId || !selectedFile || isBusy}
        >
          Reload
        </button>
      </div>

      <DirtyStateBanner dirty={isDirty} label={`${selectedFile} has local edits that are not saved yet.`} />

      <AuthoringStudioProDashboard
        activeTool={activeAuthoringTool}
        selectedWorldId={selectedWorldId}
        selectedFile={selectedFile}
        isDirty={isDirty}
        validation={validation}
        preview={preview}
        onOpenTool={handleSelectAuthoringTool}
      />

      <div className="authoring-workspace">
        <WorldFileTree
          files={usableFiles}
          selectedFile={selectedFile}
          validation={validation}
          onSelectFile={(fileName) => {
            if (isDirty && !confirmDangerousAction("Discard unsaved local edits and switch files?")) {
              return;
            }
            setSelectedFile(fileName);
          }}
        />

        <section className="authoring-editor-pane">
          <div className="authoring-pane-header">
            <div>
              <h2>{selectedFile}</h2>
              <p className="muted">{fileCategoryLabel(selectedFile)}</p>
            </div>
            <span className="badge">{viewMode === "form" ? "Form" : "Raw YAML"}</span>
          </div>
          {viewMode === "form" && FORM_SUPPORTED_FILES.has(selectedFile) ? (
            <AuthoringFormEditor
              fileName={selectedFile}
              entities={parsedEntities}
              selectedEntity={selectedEntity}
              selectedEntityId={selectedEntityId}
              disabled={disabled}
              onSelectEntity={setSelectedEntityId}
              onChangeField={(fieldName, value) => {
                if (!selectedEntity) {
                  return;
                }
                setPreview(null);
                setContent(updateEntityField(content, selectedEntity, fieldName, value));
              }}
            />
          ) : (
            <textarea
              className="yaml-editor"
              value={content}
              onChange={(event) => {
                setPreview(null);
                setContent(event.target.value);
              }}
              spellCheck={false}
              disabled={disabled}
            />
          )}
        </section>

        <ValidationPanel
          validation={validation}
          preview={preview}
          onSelectIssue={(issue) => {
            setSelectedIssuePath(issue.path);
            if (issue.file && usableFiles.includes(issue.file)) {
              if (isDirty && issue.file !== selectedFile && !confirmDangerousAction("Discard unsaved local edits and switch files?")) {
                return;
              }
              setSelectedFile(issue.file);
            }
          }}
        />

        <AuthoringPreviewPanel
          fileName={selectedFile}
          content={content}
          validation={validation}
          preview={preview}
          entities={parsedEntities}
          selectedEntity={selectedEntity}
        />
      </div>

      {selectedWorldId && (
        <>
          <AuthoringSection
            toolId="project_dashboard"
            activeTool={activeAuthoringTool}
            title="Project Dashboard"
            description="Current world, branch, validation, quality, packages, and recent local edits."
          >
            <AuthoringProjectDashboardPanel
              worldId={selectedWorldId}
              onOpenEditor={handleSelectAuthoringTool}
            />
            <ProductionPipelineDashboardPanel
              worldId={selectedWorldId}
              onOpenEditor={handleSelectAuthoringTool}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="map"
            activeTool={activeAuthoringTool}
            title="Map"
            description="Visual map authoring for locations, exits, coordinates, regions, and visibility."
          >
            <MapEditorPanel worldId={selectedWorldId} authoringDisabled={worlds.length === 0} />
          </AuthoringSection>

          <AuthoringSection
            toolId="quests"
            activeTool={activeAuthoringTool}
            title="Quests"
            description="Graph-based quest editing. Preview converts graph changes back to quests.yaml before saving."
          >
            <QuestGraphEditor
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContent, validationResult) => {
                setSelectedFile("quests.yaml");
                setContent(yamlContent);
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Quest graph preview converted to YAML. Use Preview/Save to persist."
                    : "Quest graph preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="npc_goals"
            activeTool={activeAuthoringTool}
            title="NPC Goals"
            description="Structured NPC goal and planning authoring. Hidden NPC data remains authoring-only."
          >
            <NPCGoalEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContent, validationResult) => {
                setSelectedFile("npcs.yaml");
                setContent(yamlContent);
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "NPC goal preview converted to YAML. Use Preview/Save to persist."
                    : "NPC goal preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="economy"
            activeTool={activeAuthoringTool}
            title="Items / Economy"
            description="Local item, price, and merchant inventory editing. Player shop views stay backend-filtered."
          >
            <ItemEconomyEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContents, validationResult) => {
                setSelectedFile("items.yaml");
                const nextContent = yamlContents["items.yaml"];
                if (nextContent) {
                  setContent(nextContent);
                }
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Item/economy preview converted to YAML. Use Preview/Save to persist."
                    : "Item/economy preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="advanced_modules"
            activeTool={activeAuthoringTool}
            title="Advanced Modules"
            description="Module authoring dashboard for tactical combat, economy simulation, faction war, magic, hacking, crafting, deduction, survival, and cultivation."
          >
            <AdvancedModuleAuthoringPanel worldId={selectedWorldId} projectId={projectId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="rumor_crime"
            activeTool={activeAuthoringTool}
            title="Rumors / Crime"
            description="Social consequence authoring with hidden-fact leakage warnings and validator checks."
          >
            <RumorCrimeConsequenceEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContents, validationResult) => {
                setSelectedFile("rumors.yaml");
                const nextContent = yamlContents["rumors.yaml"];
                if (nextContent) {
                  setContent(nextContent);
                }
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Rumor/crime consequence preview converted to YAML. Use Preview/Save to persist."
                    : "Rumor/crime consequence preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="example_dialogue"
            activeTool={activeAuthoringTool}
            title="Example Dialogue"
            description="Style-only dialogue samples for RP prompts. They never become facts or NPC knowledge."
          >
            <ExampleDialogueManagerPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContent, validationResult) => {
                setSelectedFile("example_dialogues.yaml");
                setContent(yamlContent);
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Example dialogue preview converted to YAML. Use Preview/Save to persist."
                    : "Example dialogue preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="rp_characters"
            activeTool={activeAuthoringTool}
            title="RP Characters"
            description="Roleplay character profiles, voice, emotions, safe imports, and safe exports."
          >
            <RPCharacterAuthoringPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContents, validationResult) => {
                const nextFile = yamlContents["npcs.yaml"] ? "npcs.yaml" : "example_dialogues.yaml";
                setSelectedFile(nextFile);
                const nextContent = yamlContents[nextFile];
                if (nextContent) {
                  setContent(nextContent);
                }
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "RP character preview converted to YAML. Use Preview/Save to persist."
                    : "RP character preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="dialogue_scenes"
            activeTool={activeAuthoringTool}
            title="Dialogue Scenes"
            description="Draft reusable dialogue scene templates. They never start active DialogueSession objects."
          >
            <DialogueSceneEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContent, validationResult) => {
                setSelectedFile("dialogue_scenes.yaml");
                setContent(yamlContent);
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Dialogue scene preview converted to YAML. Use Preview/Save to persist."
                    : "Dialogue scene preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="group_rp_scenes"
            activeTool={activeAuthoringTool}
            title="Group RP Scenes"
            description="Author multi-NPC group scene templates without starting active group dialogue."
          >
            <GroupRPSceneEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContent, validationResult) => {
                setSelectedFile("group_rp_scenes.yaml");
                setContent(yamlContent);
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Group RP scene preview converted to YAML. Use Preview/Save to persist."
                    : "Group RP scene preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="social"
            activeTool={activeAuthoringTool}
            title="Factions / Relationships"
            description="Faction and NPC relationship authoring. Player graphs only receive known, visible relationships."
          >
            <SocialGraphEditorPanel
              worldId={selectedWorldId}
              onPreviewYaml={(yamlContents, validationResult) => {
                const nextFile = yamlContents["factions.yaml"] ? "factions.yaml" : "relationships.yaml";
                setSelectedFile(nextFile);
                const nextContent = yamlContents[nextFile];
                if (nextContent) {
                  setContent(nextContent);
                }
                setPreview(null);
                setValidation(validationResult);
                setMessage(
                  validationResult.ok
                    ? "Social graph preview converted to YAML. Use Preview/Save to persist."
                    : "Social graph preview has validation errors."
                );
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="validation"
            activeTool={activeAuthoringTool}
            title="Validation"
            description="Authoring-only validation graph for files, references, and visibility risks."
          >
            <ValidationGraphPanel
              worldId={selectedWorldId}
              onSelectIssue={(issue) => {
                setSelectedIssuePath(issue.path);
                if (issue.file && usableFiles.includes(issue.file)) {
                  if (isDirty && issue.file !== selectedFile && !confirmDangerousAction("Discard unsaved local edits and switch files?")) {
                    return;
                  }
                  setSelectedFile(issue.file);
                }
              }}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="scenarios"
            activeTool={activeAuthoringTool}
            title="Scenario Regression Authoring"
            description="Create and validate local regression cases. Preview never writes disk."
          >
            <ScenarioRegressionAuthoringPanel selectedWorldId={selectedWorldId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="templates"
            activeTool={activeAuthoringTool}
            title="Templates"
            description="Local scenario templates. Preview never writes disk; apply still validates content."
          >
            <ScenarioTemplatePanel />
          </AuthoringSection>

          <AuthoringSection
            toolId="template_wizard"
            activeTool={activeAuthoringTool}
            title="Template Wizard"
            description="Guided local template drafts for worlds, quests, characters, scenes, factions, and mysteries."
          >
            <TemplateWizardPanel worldId={selectedWorldId} />
            <BatchLorebookClassificationPanel worldId={selectedWorldId} />
            <ScriptPackageBuilderPanel worldId={selectedWorldId} />
            <CampaignStarterKitBuilderPanel />
          </AuthoringSection>

          <AuthoringSection
            toolId="world_pack_wizard"
            activeTool={activeAuthoringTool}
            title="World Pack Wizard"
            description="Create a new local world-pack draft, preview files, validate, and explicitly apply to worlds."
          >
            <WorldPackWizardPanel />
          </AuthoringSection>

          <AuthoringSection
            toolId="npc_pack_generator"
            activeTool={activeAuthoringTool}
            title="NPC Pack Generator"
            description="Generate local NPC pack drafts with RP profiles, voice profiles, relationships, goals, and schedules."
          >
            <NPCPackGeneratorPanel worldId={selectedWorldId} onOpenEditor={setActiveAuthoringTool} />
          </AuthoringSection>

          <AuthoringSection
            toolId="quest_pack_generator"
            activeTool={activeAuthoringTool}
            title="Quest Pack Generator"
            description="Generate local questline drafts with facts, quest graph preview, scenario regression candidates, and quality checks."
          >
            <QuestPackGeneratorPanel worldId={selectedWorldId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="location_clusters"
            activeTool={activeAuthoringTool}
            title="Location Cluster Templates"
            description="Preview and apply connected location groups through the map validation gate."
          >
            <LocationClusterTemplatePanel worldId={selectedWorldId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="action_mods"
            activeTool={activeAuthoringTool}
            title="Action Mod Editor"
            description="Create declarative local actions, preview effects, validate DSL paths, and export module packages."
          >
            <ActionModEditorPanel worldId={selectedWorldId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="merge_assistant"
            activeTool={activeAuthoringTool}
            title="Merge Assistant"
            description="Compare two local world branches, resolve content conflicts, and save only after validation."
          >
            <WorldMergeAssistantPanel worldId={selectedWorldId} />
          </AuthoringSection>

          <AuthoringSection
            toolId="diff_review"
            activeTool={activeAuthoringTool}
            title="Content Diff Review"
            description="Review file, entity, graph, package, schema, visibility, and RP profile changes."
          >
            <ContentDiffReviewPanel
              worldId={selectedWorldId}
              fileName={selectedFile}
              content={content}
              onJump={(toolId) => setActiveAuthoringTool(toolId)}
            />
          </AuthoringSection>

          <AuthoringSection
            toolId="library"
            activeTool={activeAuthoringTool}
            title="Local Content Library"
            description="Browse, validate, import, and export local content without exposing sensitive paths."
          >
            <LocalContentLibraryPanel onOpenEditor={setActiveAuthoringTool} />
          </AuthoringSection>
        </>
      )}

      <SuccessPanel message={message} />
      <ErrorPanel message={error} />
      {selectedIssuePath && (
        <p className="muted">
          Selected issue path: <code>{selectedIssuePath}</code>
        </p>
      )}
      <ModManagerPanel />
    </section>
  );
}

function GroupRPSceneEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContent: string, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<GroupRPSceneAuthoring | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [safePreview, setSafePreview] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const referenceIndex = useReferenceIndex(worldId);

  useEffect(() => {
    void loadScenes();
  }, [worldId]);

  async function loadScenes() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchGroupRPSceneAuthoring(worldId);
      setGraph(response);
      setSelectedTemplateId(response.templates[0]?.id ?? "");
      setValidation(null);
      setSafePreview({});
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelected(updater: (template: GroupRPSceneTemplate) => GroupRPSceneTemplate) {
    if (!graph || !selectedTemplateId) {
      return;
    }
    setGraph({
      ...graph,
      templates: graph.templates.map((template) => template.id === selectedTemplateId ? updater(template) : template)
    });
  }

  function addTemplate() {
    if (!graph) {
      return;
    }
    const id = nextUniqueId("group_rp_scene", graph.templates.map((template) => template.id));
    const template: GroupRPSceneTemplate = {
      id,
      name: "New Group RP Scene",
      scene_type: "meeting",
      participant_ids: ["harlan"],
      required_roles: [{ role_id: "speaker", npc_id: "harlan", label: "Speaker", required: true }],
      location_id: "blacksmith",
      turn_order_policy: "round_robin",
      speaker_selection_policy: "deterministic",
      scene_mood: "mist_tension",
      starting_tension: 30,
      opening_public_context: "",
      allowed_topics: [],
      forbidden_topics: [],
      exit_conditions: [],
      allow_dead_participants: false
    };
    setGraph({ ...graph, templates: [...graph.templates, template] });
    setSelectedTemplateId(id);
  }

  function deleteSelected() {
    if (!graph || !selectedTemplateId) {
      return;
    }
    if (!confirmDangerousAction(`Delete group RP scene "${selectedTemplateId}" from this draft?`)) {
      return;
    }
    const nextTemplates = graph.templates.filter((template) => template.id !== selectedTemplateId);
    setGraph({ ...graph, templates: nextTemplates });
    setSelectedTemplateId(nextTemplates[0]?.id ?? "");
  }

  async function runPreview(kind: "preview" | "validate") {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = kind === "preview"
        ? await previewGroupRPSceneAuthoring(worldId, graph)
        : await validateGroupRPSceneAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      setSafePreview(response.safe_prompt_preview);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Group RP scene draft is valid." : "Group RP scene draft has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateGroupRPSceneAuthoring(worldId, graph);
      setValidation(validationResponse.validation);
      setSafePreview(validationResponse.safe_prompt_preview);
      onPreviewYaml(validationResponse.yaml_content, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Group RP scene save blocked by validation errors.");
        return;
      }
      const confirmWarnings = validationResponse.confirmation_required;
      if (confirmWarnings && !confirmDangerousAction("Validation returned warnings. Save group RP scene changes anyway?")) {
        setMessage("Group RP scene save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Group RP scene save cancelled.");
        return;
      }
      const response = await saveGroupRPSceneAuthoring(worldId, graph, confirmWarnings);
      setGraph(response.graph);
      setValidation(response.validation);
      setSafePreview(response.safe_prompt_preview);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.saved ? "Group RP scene templates saved." : "Group RP scene templates were not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selected = graph?.templates.find((template) => template.id === selectedTemplateId) ?? null;

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Group RP Scene Authoring</h2>
          <p className="muted">Design multi-NPC scenes, roles, turn policy, tension, and safe public openings.</p>
        </div>
        <button type="button" onClick={() => void loadScenes()} disabled={isBusy}>Reload Group Scenes</button>
      </div>
      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Group Scenes</h3>
            {graph.templates.map((template) => (
              <button
                type="button"
                key={template.id}
                className={template.id === selectedTemplateId ? "active" : ""}
                onClick={() => setSelectedTemplateId(template.id)}
              >
                {template.name || template.id}
              </button>
            ))}
            <button type="button" onClick={addTemplate} disabled={isBusy}>Add Group Scene</button>
          </aside>
          <div className="graph-detail-panel">
            {selected ? (
              <section className="authoring-preview-box">
                <div className="authoring-pane-header compact">
                  <h3>Group Scene Template</h3>
                  <button type="button" onClick={deleteSelected} disabled={isBusy}>Delete Scene</button>
                </div>
                <div className="form-grid">
                  <TextInput label="Id" value={selected.id} onChange={(value) => updateSelected((template) => ({ ...template, id: value }))} />
                  <TextInput label="Name" value={selected.name} onChange={(value) => updateSelected((template) => ({ ...template, name: value }))} />
                  <TextInput label="Scene type" value={selected.scene_type} onChange={(value) => updateSelected((template) => ({ ...template, scene_type: value }))} />
                  <TextInput label="Participants" value={selected.participant_ids.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, participant_ids: commaList(value) }))} />
                  <TextInput label="Roles" value={selected.required_roles.map((role) => `${role.role_id}:${role.npc_id}`).join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, required_roles: commaList(value).map((entry) => {
                    const [roleId, npcId] = entry.split(":");
                    return { role_id: roleId || "role", npc_id: npcId || roleId || "", label: roleId || "Role", required: true };
                  }) }))} />
                  <ReferencePicker label="Location" kind="location" index={referenceIndex} value={selected.location_id} onChange={(value) => updateSelected((template) => ({ ...template, location_id: value }))} allowEmpty={false} />
                  <TextInput label="Turn order" value={selected.turn_order_policy} onChange={(value) => updateSelected((template) => ({ ...template, turn_order_policy: value }))} />
                  <TextInput label="Speaker policy" value={selected.speaker_selection_policy} onChange={(value) => updateSelected((template) => ({ ...template, speaker_selection_policy: value }))} />
                  <ReferencePicker label="Mood" kind="scene mood" index={referenceIndex} value={selected.scene_mood ?? ""} onChange={(value) => updateSelected((template) => ({ ...template, scene_mood: emptyToNull(value) }))} />
                  <NumberInput label="Starting tension" value={selected.starting_tension} onChange={(value) => updateSelected((template) => ({ ...template, starting_tension: value }))} />
                  <TextInput label="Allowed topics" value={selected.allowed_topics.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, allowed_topics: commaList(value) }))} />
                  <TextInput label="Forbidden topics" value={selected.forbidden_topics.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, forbidden_topics: commaList(value) }))} />
                  <TextInput label="Exit conditions" value={selected.exit_conditions.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, exit_conditions: commaList(value) }))} />
                </div>
                <label><input type="checkbox" checked={selected.allow_dead_participants} onChange={(event) => updateSelected((template) => ({ ...template, allow_dead_participants: event.target.checked }))} /> Allow dead/incapacitated participants</label>
                <label>Opening public context<textarea value={selected.opening_public_context} onChange={(event) => updateSelected((template) => ({ ...template, opening_public_context: event.target.value }))} /></label>
                <div className="authoring-preview-box subtle">
                  <h4>Safe group prompt preview</h4>
                  <p className="muted">{safePreview[selected.id] || "Run Preview to generate a safe group scene preview."}</p>
                </div>
              </section>
            ) : (
              <EmptyState title="No group RP scene selected." detail="Add or select a group scene template to edit." />
            )}
            <AuthoringActionBar
              onPreview={() => void runPreview("preview")}
              onValidate={() => void runPreview("validate")}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <PreviewResultPanel title="Group RP Scene Validation" validation={validation} />
          </div>
        </div>
      ) : (
        <EmptyState title="No group RP scenes loaded." detail="Load group_rp_scenes.yaml through the authoring API." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function AdvancedModuleAuthoringPanel({ worldId, projectId }: { worldId: string; projectId: string }) {
  const [modules, setModules] = useState<AdvancedModuleDashboardItem[]>([]);
  const [selectedModuleId, setSelectedModuleId] = useState<string>("tactical_combat");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [validation, setValidation] = useState<AdvancedModuleDraftValidation | null>(null);
  const [qualityGate, setQualityGate] = useState<{ passed: boolean; blockers: string[]; warnings: string[] } | null>(null);

  useEffect(() => {
    void refreshDashboard();
  }, [worldId]);

  async function refreshDashboard() {
    if (!worldId) {
      return;
    }
    setError("");
    try {
      const response = await fetchAuthoringModuleDashboard(worldId);
      setModules(response.modules);
      setSelectedModuleId((current) => current || response.modules[0]?.module_id || "tactical_combat");
    } catch (err) {
      setModules([]);
      setError(toErrorMessage(err));
    }
  }

  async function handleValidateSelected() {
    setError("");
    setValidation(null);
    try {
      const draft = await loadDraftForSelected();
      const result = await validateDraftForSelected(draft);
      setValidation(result);
      setMessage(result.ok ? "Module draft validation passed." : "Module draft validation found issues.");
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function handleQualityGate() {
    setError("");
    try {
      const response = await runProjectAdvancedModuleQualityGate(projectId);
      setQualityGate(response.quality_gate);
      setMessage(response.quality_gate.passed ? "Advanced module quality gate passed." : "Advanced module quality gate found blockers.");
    } catch (err) {
      setError(toErrorMessage(err));
    }
  }

  async function loadDraftForSelected(): Promise<Record<string, unknown>> {
    if (selectedModuleId === "economy_sim") {
      return fetchEconomySimConfig(worldId);
    }
    if (selectedModuleId === "faction_war") {
      return fetchFactionWarConfig(worldId);
    }
    return fetchTacticalCombatConfig(worldId);
  }

  async function validateDraftForSelected(draft: Record<string, unknown>): Promise<AdvancedModuleDraftValidation> {
    const payload = (draft.draft as Record<string, unknown> | undefined) ?? draft;
    if (selectedModuleId === "economy_sim") {
      return validateEconomySimDraft(worldId, payload);
    }
    if (selectedModuleId === "faction_war") {
      return validateFactionWarDraft(worldId, payload);
    }
    return validateTacticalCombatDraft(worldId, payload);
  }

  return (
    <SectionCard title="Advanced Modules" description="Local-only advanced module authoring and validation.">
      <div className="section-header">
        <div>
          <h3>Module Authoring Dashboard</h3>
          <p className="muted">Local-only advanced modules. Draft/config validation does not modify active GameState and never displays secrets or hidden details.</p>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => void refreshDashboard()}>Refresh</button>
          <button type="button" onClick={() => void handleValidateSelected()} disabled={!worldId}>Validate Draft</button>
          <button type="button" onClick={() => void handleQualityGate()}>Quality Gate</button>
        </div>
      </div>
      {modules.length === 0 ? (
        <EmptyState title="No advanced module dashboard data." detail="Enable the local authoring API to inspect module schema, actions, migration, validation, and quality status." />
      ) : (
        <div className="provider-table-wrap">
          <table className="provider-table">
            <thead><tr><th>Module</th><th>Enabled</th><th>State</th><th>Actions</th><th>Migration</th><th>Validation</th><th>Quality</th></tr></thead>
            <tbody>
              {modules.map((item) => (
                <tr key={item.module_id} className={selectedModuleId === item.module_id ? "selected-row" : ""} onClick={() => setSelectedModuleId(item.module_id)}>
                  <td>{item.module_id}</td>
                  <td>{item.enabled ? "enabled" : "disabled"}</td>
                  <td>{item.state_extension_status}</td>
                  <td>{item.actions_provided.length}</td>
                  <td>{item.migration_required ? "required" : "clear"}</td>
                  <td>{item.validation_status}</td>
                  <td>{item.quality_gate_status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="grid two-column">
        <InfoCard title="Tactical Combat" value="encounter drafts, combatants, range and cover" detail="Normal UI omits hidden combatants." />
        <InfoCard title="Economy / Faction" value="market and conflict drafts" detail="Authoring validation only; backend rules remain authoritative." />
      </div>
      {validation && (
        <StatusList
          title={validation.ok ? "Validation passed" : "Validation issues"}
          items={[...validation.errors, ...validation.warnings]}
          emptyText="No warnings or errors."
        />
      )}
      {qualityGate && (
        <StatusList
          title={qualityGate.passed ? "Quality gate passed" : "Quality gate blockers"}
          items={[...qualityGate.blockers, ...qualityGate.warnings]}
          emptyText="No blockers or warnings."
        />
      )}
      <SuccessPanel message={message} compact />
      <ErrorPanel message={error} compact />
    </SectionCard>
  );
}

function InfoCard({ title, value, detail }: { title: string; value: string; detail: string }) {
  return (
    <div className="metric-card">
      <span>{title}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </div>
  );
}

function StatusList({ title, items, emptyText }: { title: string; items: string[]; emptyText: string }) {
  return (
    <div className="validation-list">
      <h4>{title}</h4>
      {items.length === 0 ? <p className="muted">{emptyText}</p> : <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}
    </div>
  );
}

function ActionModTestHarnessPanel({ report, onRun, disabled }: { report: ActionModTestRunResponse | null; onRun: () => void; disabled: boolean }) {
  return (
    <section className="module-pro-panel">
      <div className="section-heading-row">
        <div>
          <h4>Action Mod Test Harness UI</h4>
          <p className="muted">Runs local safe checks for declarative actions. It does not execute arbitrary code, write active saves, call providers, or expose raw state_deltas.</p>
        </div>
        <button type="button" onClick={onRun} disabled={disabled}>Run Tests</button>
      </div>
      <div className="safe-summary-grid">
        <SafeSummaryCard title="Report" value={report ? (report.ok ? "passed" : "failed") : "not run"} detail={report ? `${report.passed_count}/${report.test_count} tests passed` : "Run tests after preview/validation."} />
        <SafeSummaryCard title="State mutation" value={report?.active_game_state_modified ? "blocked" : "none"} detail="Harness verifies active GameState is unchanged." />
        <SafeSummaryCard title="Raw deltas" value={report?.raw_state_deltas_included ? "blocked" : "excluded"} detail="Only StateDelta safe summaries are shown." />
      </div>
      {report ? (
        <div className="module-browser-table">
          {report.results.map((result) => (
            <div key={result.test_id} className="module-browser-row static">
              <span><strong>{result.test_id}</strong><small>{result.action_id}</small></span>
              <ValidationStatusBadge status={result.passed ? "passed" : "failed"} />
              <span>{result.expected_result_type} {"->"} {result.actual_result_type}</span>
              <span>{result.expected_state_delta_summary.join(", ") || "no StateDelta proposal"}</span>
              <span>{result.event_tags.join(", ") || "no event tags"}</span>
              <span>{result.hidden_leak_warnings.join(", ") || "no hidden leak warning"}</span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No Action Mod test report." detail="Use Run Tests to generate a local safe report from the current declarative draft." />
      )}
    </section>
  );
}

function ActionModEditorPanel({ worldId }: { worldId: string }) {
  const referenceIndex = useReferenceIndex(worldId);
  const [draft, setDraft] = useState<ActionModDraft>(() => defaultActionModDraft());
  const [selectedActionIndex, setSelectedActionIndex] = useState<number>(0);
  const [preview, setPreview] = useState<ActionModPreviewResponse | null>(null);
  const [testReport, setTestReport] = useState<ActionModTestRunResponse | null>(null);
  const [jsonError, setJsonError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  const selectedAction = draft.actions[selectedActionIndex] ?? draft.actions[0];
  const validation = preview ? actionModValidationAsAuthoring(preview.validation) : null;

  function updateDraft(update: Partial<ActionModDraft>) {
    setPreview(null);
    setTestReport(null);
    setDraft((current) => ({ ...current, ...update }));
  }

  function updateSelectedAction(update: (action: DeclarativeActionDefinition) => DeclarativeActionDefinition) {
    setPreview(null);
    setTestReport(null);
    setDraft((current) => ({
      ...current,
      actions: current.actions.map((action, index) => index === selectedActionIndex ? update(action) : action)
    }));
  }

  async function runRequest(kind: "preview" | "validate" | "export") {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      if (kind === "export") {
        const response = await exportActionModDraft(draft);
        setPreview({ local_only: response.local_only, draft, validation: response.validation, writes_to_disk: false, executes_code: false, active_game_state_modified: false, normalized_yaml: "" });
        setMessage(response.exported ? `Module package ready: ${response.file_name}` : "Export blocked by validation errors.");
        return;
      }
      const response = kind === "preview" ? await previewActionModDraft(draft) : await validateActionModDraft(draft);
      setPreview(response);
      setMessage(response.validation.ok ? `${kind === "preview" ? "Preview" : "Validation"} passed.` : "Validation found blocking errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function runTests() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await runActionModDraftTests(draft);
      setTestReport(response);
      setPreview({ local_only: response.local_only, draft, validation: response.validation, writes_to_disk: false, executes_code: false, active_game_state_modified: false, normalized_yaml: preview?.normalized_yaml ?? "" });
      setMessage(response.ok ? "Action Mod tests passed." : "Action Mod tests found blockers.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function addAction() {
    const nextAction = defaultDeclarativeAction(`module.action_${draft.actions.length + 1}`);
    setDraft((current) => ({ ...current, actions: [...current.actions, nextAction] }));
    setSelectedActionIndex(draft.actions.length);
  }

  function removeSelectedAction() {
    if (draft.actions.length <= 1) {
      return;
    }
    setDraft((current) => ({ ...current, actions: current.actions.filter((_, index) => index !== selectedActionIndex) }));
    setSelectedActionIndex(0);
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Action Mod Editor</h2>
          <p className="muted">Declarative YAML only. No execute_code field, no scripts, no active GameState writes.</p>
        </div>
        <AuthoringActionBar
          onPreview={() => void runRequest("preview")}
          onValidate={() => void runRequest("validate")}
          onSave={() => void runRequest("export")}
          previewLabel="Preview"
          validateLabel="Validate"
          saveLabel="Export Module"
          disabled={isBusy}
        />
      </div>

      <div className="template-grid">
        <TextInput label="Module id" value={draft.module_id} onChange={(value) => updateDraft({ module_id: value })} />
        <TextInput label="Module name" value={draft.name} onChange={(value) => updateDraft({ name: value })} />
        <TextInput label="Version" value={draft.version} onChange={(value) => updateDraft({ version: value })} />
      </div>

      <div className="authoring-workspace compact">
        <aside className="entity-list">
          <button type="button" onClick={addAction} disabled={isBusy}>Add Action</button>
          <button type="button" onClick={removeSelectedAction} disabled={isBusy || draft.actions.length <= 1}>Remove</button>
          {draft.actions.map((action, index) => (
            <button
              type="button"
              key={`${action.id}:${index}`}
              className={index === selectedActionIndex ? "active" : ""}
              onClick={() => setSelectedActionIndex(index)}
            >
              {action.label || action.id}
            </button>
          ))}
        </aside>

        {selectedAction && (
          <section className="authoring-editor-pane">
            <div className="template-grid">
              <TextInput label="Action id" value={selectedAction.id} onChange={(value) => updateSelectedAction((action) => ({ ...action, id: value, event_type: action.event_type || `${value}.resolved` }))} />
              <TextInput label="Label" value={selectedAction.label} onChange={(value) => updateSelectedAction((action) => ({ ...action, label: value }))} />
              <TextInput label="Aliases" value={selectedAction.aliases.join(", ")} onChange={(value) => updateSelectedAction((action) => ({ ...action, aliases: commaList(value) }))} />
              <label>Category<select value={selectedAction.category} onChange={(event) => updateSelectedAction((action) => ({ ...action, category: event.target.value }))}>{["general", "magic", "hacking", "crafting", "investigation", "travel", "stealth", "combat", "social", "faction", "domain"].map((category) => <option key={category} value={category}>{category}</option>)}</select></label>
              <NumberInput label="Time cost" value={selectedAction.time_cost} onChange={(value) => updateSelectedAction((action) => ({ ...action, time_cost: Math.max(0, value) }))} />
              <TextInput label="Event type" value={selectedAction.event_type} onChange={(value) => updateSelectedAction((action) => ({ ...action, event_type: value }))} />
            </div>

            <div className="template-grid">
              <label>Target kind<select value={selectedAction.target_specs[0]?.kind ?? "current_location"} onChange={(event) => updateSelectedAction((action) => ({ ...action, target_specs: [{ ...(action.target_specs[0] ?? { required: true, allowed_ids: [] }), kind: event.target.value as DeclarativeActionDefinition["target_specs"][number]["kind"] }] }))}>{["self", "current_location", "location", "object", "npc"].map((kind) => <option key={kind} value={kind}>{kind}</option>)}</select></label>
              <label><input type="checkbox" checked={selectedAction.target_specs[0]?.required ?? true} onChange={(event) => updateSelectedAction((action) => ({ ...action, target_specs: [{ ...(action.target_specs[0] ?? { kind: "current_location", allowed_ids: [] }), required: event.target.checked }] }))} /> Target required</label>
              <ReferencePicker label="Allowed item target" kind="item" index={referenceIndex} value={selectedAction.target_specs[0]?.allowed_ids[0] ?? ""} onChange={(value) => updateSelectedAction((action) => ({ ...action, target_specs: [{ ...(action.target_specs[0] ?? { kind: "object", required: true }), allowed_ids: value ? [value] : [] }] }))} />
              <ReferencePicker label="Required visible fact" kind="fact" index={referenceIndex} value={selectedAction.affordance_requirements.required_visible_facts[0] ?? ""} onChange={(value) => updateSelectedAction((action) => ({ ...action, affordance_requirements: { ...action.affordance_requirements, required_visible_facts: value ? [value] : [] } }))} />
            </div>

            <div className="template-grid">
              <TextInput label="StateDelta path" value={selectedAction.outcomes.success?.state_delta_templates[0]?.path ?? ""} onChange={(value) => updateSelectedSuccessOutcome(selectedAction, updateSelectedAction, { path: value })} />
              <label>StateDelta op<select value={selectedAction.outcomes.success?.state_delta_templates[0]?.operation ?? "set"} onChange={(event) => updateSelectedSuccessOutcome(selectedAction, updateSelectedAction, { operation: event.target.value as DeclarativeActionDefinition["state_delta_templates"][number]["operation"] })}>{["set", "inc", "add", "remove"].map((op) => <option key={op} value={op}>{op}</option>)}</select></label>
              <TextInput label="Visible facts" value={(selectedAction.outcomes.success?.visible_facts ?? []).join(", ")} onChange={(value) => updateSelectedOutcomeList(updateSelectedAction, "visible_facts", commaList(value))} />
              <TextInput label="Hidden facts" value={(selectedAction.outcomes.success?.hidden_facts ?? []).join(", ")} onChange={(value) => updateSelectedOutcomeList(updateSelectedAction, "hidden_facts", commaList(value))} />
              <label><input type="checkbox" checked={selectedAction.outcomes.success?.hidden_outcome ?? false} onChange={(event) => updateSelectedOutcomeFlag(updateSelectedAction, "hidden_outcome", event.target.checked)} /> Hidden outcome</label>
              <label><input type="checkbox" checked={selectedAction.visibility_policy.include_target_in_visible_facts} onChange={(event) => updateSelectedAction((action) => ({ ...action, visibility_policy: { ...action.visibility_policy, include_target_in_visible_facts: event.target.checked } }))} /> Include target in visible result</label>
              <label><input type="checkbox" checked={selectedAction.visibility_policy.include_current_location_in_visible_facts} onChange={(event) => updateSelectedAction((action) => ({ ...action, visibility_policy: { ...action.visibility_policy, include_current_location_in_visible_facts: event.target.checked } }))} /> Include current location</label>
            </div>

            <label>
              Preconditions JSON
              <textarea className="yaml-editor short" value={JSON.stringify(selectedAction.preconditions, null, 2)} onChange={(event) => updateJsonList(event.target.value, (items) => updateSelectedAction((action) => ({ ...action, preconditions: items })), setJsonError)} />
            </label>
            <label>
              Checks JSON
              <textarea className="yaml-editor short" value={JSON.stringify(selectedAction.checks, null, 2)} onChange={(event) => updateJsonList(event.target.value, (items) => updateSelectedAction((action) => ({ ...action, checks: items })), setJsonError)} />
            </label>
          </section>
        )}

        <section className="authoring-preview-side">
          <PreviewResultPanel title="Action Mod Validation" validation={validation} previewContent={preview?.normalized_yaml} />
          {jsonError && <ErrorPanel message={jsonError} compact />}
          <SuccessPanel message={message} />
          <ErrorPanel message={error} />
        </section>
      </div>
      <ActionModTestHarnessPanel report={testReport} onRun={() => void runTests()} disabled={isBusy || Boolean(jsonError)} />
    </section>
  );
}

function defaultActionModDraft(): ActionModDraft {
  return {
    module_id: "local_action_mod",
    name: "Local Action Mod",
    version: "0.1.0",
    actions: [defaultDeclarativeAction("module.pray")]
  };
}

function defaultDeclarativeAction(actionId: string): DeclarativeActionDefinition {
  return {
    id: actionId,
    label: "Pray",
    aliases: ["pray"],
    category: "general",
    target_specs: [{ kind: "current_location", required: true, allowed_ids: [] }],
    affordance_requirements: { required_visible_facts: [], required_flags: {} },
    time_cost: 1,
    preconditions: [],
    checks: [],
    outcomes: { success: defaultDeclarativeOutcome() },
    state_delta_templates: [],
    event_type: `${actionId}.resolved`,
    visibility_policy: {
      hidden_outcome_player_visible: false,
      include_target_in_visible_facts: true,
      include_current_location_in_visible_facts: true
    },
    narrator_hints: { style: "", safe_summary: "", hidden_summary: "" }
  };
}

function defaultDeclarativeOutcome(): DeclarativeOutcome {
  return {
    success_level: "success",
    reason: "Resolved by declarative local rules.",
    state_delta_templates: [{ operation: "set", path: "flags.local_action_resolved", value: true }],
    visible_facts: [],
    hidden_facts: [],
    hidden_outcome: false
  };
}

function updateSelectedSuccessOutcome(
  selectedAction: DeclarativeActionDefinition,
  updateSelectedAction: (update: (action: DeclarativeActionDefinition) => DeclarativeActionDefinition) => void,
  templatePatch: Partial<DeclarativeActionDefinition["state_delta_templates"][number]>
) {
  const currentOutcome = selectedAction.outcomes.success ?? defaultDeclarativeOutcome();
  const currentTemplate = currentOutcome.state_delta_templates[0] ?? defaultDeclarativeOutcome().state_delta_templates[0];
  updateSelectedAction((action) => ({
    ...action,
    outcomes: {
      ...action.outcomes,
      success: {
        ...(action.outcomes.success ?? defaultDeclarativeOutcome()),
        state_delta_templates: [{ ...currentTemplate, ...templatePatch }]
      }
    }
  }));
}

function updateSelectedOutcomeList(
  updateSelectedAction: (update: (action: DeclarativeActionDefinition) => DeclarativeActionDefinition) => void,
  key: "visible_facts" | "hidden_facts",
  value: string[]
) {
  updateSelectedAction((action) => ({
    ...action,
    outcomes: {
      ...action.outcomes,
      success: {
        ...(action.outcomes.success ?? defaultDeclarativeOutcome()),
        [key]: value
      }
    }
  }));
}

function updateSelectedOutcomeFlag(
  updateSelectedAction: (update: (action: DeclarativeActionDefinition) => DeclarativeActionDefinition) => void,
  key: "hidden_outcome",
  value: boolean
) {
  updateSelectedAction((action) => ({
    ...action,
    outcomes: {
      ...action.outcomes,
      success: {
        ...(action.outcomes.success ?? defaultDeclarativeOutcome()),
        [key]: value
      }
    }
  }));
}

function updateJsonList(
  raw: string,
  onValid: (items: Record<string, unknown>[]) => void,
  setError: (message: string) => void
) {
  try {
    if (containsForbiddenActionModLogic(raw)) {
      setError("Action Mod DSL must stay declarative. exec/eval/code/script/function fields are blocked.");
      return;
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.some((item) => item === null || typeof item !== "object" || Array.isArray(item))) {
      setError("JSON must be an array of objects.");
      return;
    }
    setError("");
    onValid(parsed as Record<string, unknown>[]);
  } catch {
    setError("Invalid JSON.");
  }
}

function containsForbiddenActionModLogic(raw: string): boolean {
  return /\b(exec|eval|function|script|python|javascript|read_secrets|access_network|access_filesystem)\b/i.test(raw);
}

function actionModValidationAsAuthoring(report: ActionModPreviewResponse["validation"]): AuthoringValidation {
  return {
    world_id: report.module_id,
    ok: report.ok,
    errors: report.errors,
    warnings: report.warnings,
    suggestions: []
  };
}

function DialogueSceneEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContent: string, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<DialogueSceneAuthoring | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [promptPreview, setPromptPreview] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const referenceIndex = useReferenceIndex(worldId);

  useEffect(() => {
    void loadScenes();
  }, [worldId]);

  async function loadScenes() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchDialogueSceneAuthoring(worldId);
      setGraph(response);
      setSelectedTemplateId(response.templates[0]?.id ?? "");
      setValidation(null);
      setPromptPreview({});
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelected(updater: (template: DialogueSceneTemplate) => DialogueSceneTemplate) {
    if (!graph || !selectedTemplateId) {
      return;
    }
    setGraph({
      ...graph,
      templates: graph.templates.map((template) => template.id === selectedTemplateId ? updater(template) : template)
    });
  }

  function addTemplate() {
    if (!graph) {
      return;
    }
    const id = nextUniqueId("dialogue_scene", graph.templates.map((template) => template.id));
    const template: DialogueSceneTemplate = {
      id,
      name: "New Dialogue Scene",
      participant_ids: ["harlan"],
      focus_npc_id: "harlan",
      location_id: "blacksmith",
      dialogue_mode: "focused",
      scene_mood: "mist_tension",
      rp_prompt_profile_id: "default_safe",
      opening_context: "",
      allowed_topics: [],
      forbidden_topics: [],
      required_visible_facts: [],
      possible_outcomes: []
    };
    setGraph({ ...graph, templates: [...graph.templates, template] });
    setSelectedTemplateId(id);
  }

  function deleteSelected() {
    if (!graph || !selectedTemplateId) {
      return;
    }
    if (!confirmDangerousAction(`Delete dialogue scene "${selectedTemplateId}" from this draft?`)) {
      return;
    }
    const nextTemplates = graph.templates.filter((template) => template.id !== selectedTemplateId);
    setGraph({ ...graph, templates: nextTemplates });
    setSelectedTemplateId(nextTemplates[0]?.id ?? "");
  }

  async function runPreview(kind: "preview" | "validate") {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = kind === "preview"
        ? await previewDialogueSceneAuthoring(worldId, graph)
        : await validateDialogueSceneAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      setPromptPreview(response.prompt_preview);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Dialogue scene draft is valid." : "Dialogue scene draft has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateDialogueSceneAuthoring(worldId, graph);
      setValidation(validationResponse.validation);
      setPromptPreview(validationResponse.prompt_preview);
      onPreviewYaml(validationResponse.yaml_content, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Dialogue scene save blocked by validation errors.");
        return;
      }
      const confirmWarnings = validationResponse.confirmation_required;
      if (confirmWarnings && !confirmDangerousAction("Validation returned warnings. Save dialogue scene changes anyway?")) {
        setMessage("Dialogue scene save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Dialogue scene save cancelled.");
        return;
      }
      const response = await saveDialogueSceneAuthoring(worldId, graph, confirmWarnings);
      setGraph(response.graph);
      setValidation(response.validation);
      setPromptPreview(response.prompt_preview);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.saved ? "Dialogue scene templates saved." : "Dialogue scene templates were not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selected = graph?.templates.find((template) => template.id === selectedTemplateId) ?? null;

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Dialogue Scene Editor</h2>
          <p className="muted">Local scene templates for DialogueManager. Preview and validation do not start sessions.</p>
        </div>
        <button type="button" onClick={() => void loadScenes()} disabled={isBusy}>Reload Scenes</button>
      </div>
      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Scenes</h3>
            {graph.templates.map((template) => (
              <button
                type="button"
                key={template.id}
                className={template.id === selectedTemplateId ? "active" : ""}
                onClick={() => setSelectedTemplateId(template.id)}
              >
                {template.name || template.id}
              </button>
            ))}
            <button type="button" onClick={addTemplate} disabled={isBusy}>Add Scene</button>
          </aside>
          <div className="graph-detail-panel">
            {selected ? (
              <section className="authoring-preview-box">
                <div className="authoring-pane-header compact">
                  <h3>Scene Template</h3>
                  <button type="button" onClick={deleteSelected} disabled={isBusy}>Delete Scene</button>
                </div>
                <div className="form-grid">
                  <TextInput label="Id" value={selected.id} onChange={(value) => updateSelected((template) => ({ ...template, id: value }))} />
                  <TextInput label="Name" value={selected.name} onChange={(value) => updateSelected((template) => ({ ...template, name: value }))} />
                  <TextInput label="Participants" value={selected.participant_ids.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, participant_ids: commaList(value) }))} />
                  <ReferencePicker label="Focus NPC" kind="NPC" index={referenceIndex} value={selected.focus_npc_id} onChange={(value) => updateSelected((template) => ({ ...template, focus_npc_id: value }))} allowEmpty={false} />
                  <ReferencePicker label="Location" kind="location" index={referenceIndex} value={selected.location_id} onChange={(value) => updateSelected((template) => ({ ...template, location_id: value }))} allowEmpty={false} />
                  <TextInput label="Dialogue mode" value={selected.dialogue_mode} onChange={(value) => updateSelected((template) => ({ ...template, dialogue_mode: value }))} />
                  <ReferencePicker label="Scene mood" kind="scene mood" index={referenceIndex} value={selected.scene_mood ?? ""} onChange={(value) => updateSelected((template) => ({ ...template, scene_mood: emptyToNull(value) }))} />
                  <ReferencePicker label="RP prompt profile" kind="prompt profile" index={referenceIndex} value={selected.rp_prompt_profile_id ?? ""} onChange={(value) => updateSelected((template) => ({ ...template, rp_prompt_profile_id: emptyToNull(value) }))} />
                  <TextInput label="Allowed topics" value={selected.allowed_topics.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, allowed_topics: commaList(value) }))} />
                  <TextInput label="Forbidden topics" value={selected.forbidden_topics.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, forbidden_topics: commaList(value) }))} />
                  <TextInput label="Required visible facts" value={selected.required_visible_facts.join(", ")} onChange={(value) => updateSelected((template) => ({ ...template, required_visible_facts: commaList(value) }))} />
                </div>
                <label>Opening context<textarea value={selected.opening_context} onChange={(event) => updateSelected((template) => ({ ...template, opening_context: event.target.value }))} /></label>
                <div className="authoring-preview-box subtle">
                  <h4>Prompt-safe preview</h4>
                  <p className="muted">{promptPreview[selected.id] || "Run Preview to generate a safe prompt preview."}</p>
                </div>
              </section>
            ) : (
              <EmptyState title="No dialogue scene selected." detail="Add or select a scene template to edit." />
            )}
            <AuthoringActionBar
              onPreview={() => void runPreview("preview")}
              onValidate={() => void runPreview("validate")}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <PreviewResultPanel title="Dialogue Scene Validation" validation={validation} />
          </div>
        </div>
      ) : (
        <EmptyState title="No dialogue scenes loaded." detail="Load dialogue_scenes.yaml through the authoring API." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function RPCharacterAuthoringPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContents: Record<string, string>, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<RPCharacterAuthoring | null>(null);
  const [selectedNpcId, setSelectedNpcId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [importDraft, setImportDraft] = useState<string>("");
  const [importReport, setImportReport] = useState<CharacterCardImportReport | null>(null);
  const [batchImportDraft, setBatchImportDraft] = useState<string>("");
  const [batchImportReport, setBatchImportReport] = useState<BatchCharacterCardImportReport | null>(null);
  const [selectedBatchNames, setSelectedBatchNames] = useState<string[]>([]);
  const [safeExport, setSafeExport] = useState<string>("");
  const [exportProfiles, setExportProfiles] = useState<ExportProfile[]>([]);
  const [selectedExportProfileId, setSelectedExportProfileId] = useState<string>("safe");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const referenceIndex = useReferenceIndex(worldId);

  useEffect(() => {
    void loadCharacters();
    void loadImportExportProfiles();
  }, [worldId]);

  async function loadImportExportProfiles() {
    try {
      const catalog = await fetchImportExportProfiles();
      setExportProfiles(catalog.export_profiles);
      setSelectedExportProfileId((current) =>
        catalog.export_profiles.some((profile) => profile.profile_id === current)
          ? current
          : catalog.export_profiles[0]?.profile_id ?? "safe"
      );
    } catch {
      setExportProfiles([]);
      setSelectedExportProfileId("safe");
    }
  }

  async function loadCharacters() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchRPCharacterAuthoring(worldId);
      setGraph(response);
      setSelectedNpcId(response.characters[0]?.npc_id ?? "");
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelected(updater: (character: RPCharacterAuthoringProfile) => RPCharacterAuthoringProfile) {
    if (!graph || !selectedNpcId) {
      return;
    }
    setGraph({
      ...graph,
      characters: graph.characters.map((character) => character.npc_id === selectedNpcId ? updater(character) : character)
    });
  }

  async function handlePreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await previewRPCharacterAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "RP character preview is valid." : "RP character preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await validateRPCharacterAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "RP character validation passed." : "RP character validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const validationResponse = await validateRPCharacterAuthoring(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_contents, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("RP character save blocked by validation errors.");
        return;
      }
      const confirmWarnings = validationResponse.confirmation_required;
      if (confirmWarnings && !confirmDangerousAction("Validation returned warnings. Save RP character changes anyway?")) {
        setMessage("RP character save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("RP character save cancelled.");
        return;
      }
      const response = await saveRPCharacterAuthoring(worldId, graph, confirmWarnings);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.saved ? "RP character data saved." : "RP character data was not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleImportPreview() {
    const raw = importDraft.trim();
    if (!raw) {
      setMessage("Paste a local character card payload first.");
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await previewRPCharacterImport(worldId, raw);
      setImportReport(response);
      setMessage(response.ok ? "Character card import preview is safe." : "Character card import contains unsafe entries.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function batchImportTexts(): string[] {
    return batchImportDraft
      .split(/\n---+\n/g)
      .map((value) => value.trim())
      .filter(Boolean);
  }

  async function handleBatchImportPreview() {
    const texts = batchImportTexts();
    if (!texts.length) {
      setMessage("Paste one or more character cards separated by ---.");
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await previewBatchCharacterCardImport(worldId, texts);
      setBatchImportReport(response);
      setSelectedBatchNames(response.candidate_characters.map((candidate) => String(candidate.name ?? "")));
      setMessage(`Batch preview parsed ${response.parsed_count} cards; unsafe ${response.unsafe_count}.`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleBatchApplyDraft() {
    const texts = batchImportTexts();
    setIsBusy(true);
    setError("");
    try {
      const response = await applyBatchCharacterCardImportDraft(worldId, texts, selectedBatchNames);
      setBatchImportReport(response);
      setSafeExport(JSON.stringify(response.character_pack_draft, null, 2));
      setMessage("Batch draft prepared. It has not been written to the world pack.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleBatchExportPack() {
    const texts = batchImportTexts();
    setIsBusy(true);
    setError("");
    try {
      const response = await exportBatchCharacterCardPack(worldId, texts, selectedBatchNames);
      setSafeExport(JSON.stringify(response, null, 2));
      setMessage("Batch character pack draft exported.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSafeExport() {
    if (!selectedNpcId) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await exportSafeRPCharacterCard(worldId, selectedNpcId);
      setSafeExport(JSON.stringify(response.card, null, 2));
      setMessage(`Safe export ready. Excluded: ${response.excluded_fields.join(", ")}`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCharacterPackExport() {
    if (!selectedNpcId) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await exportCharacterPack(worldId, [selectedNpcId], selectedExportProfileId);
      setSafeExport(JSON.stringify(response, null, 2));
      setMessage(`Character pack export ready with profile ${selectedExportProfileId}.`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selected = graph?.characters.find((character) => character.npc_id === selectedNpcId) ?? null;

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>RP Character Editor</h2>
          <p className="muted">Local-only RP profile, voice, emotion, example dialogue, import report, and safe export editor.</p>
        </div>
        <button type="button" onClick={() => void loadCharacters()} disabled={isBusy}>Reload Characters</button>
      </div>

      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Characters</h3>
            {graph.characters.map((character) => (
              <button
                type="button"
                key={character.npc_id}
                className={character.npc_id === selectedNpcId ? "active" : ""}
                onClick={() => setSelectedNpcId(character.npc_id)}
              >
                {character.name || character.npc_id}
                {character.safety_flags.length ? " *" : ""}
              </button>
            ))}
          </aside>

          <div className="graph-detail-panel">
            {selected ? (
              <>
                <section className="authoring-preview-box">
                  <h3>Character Card</h3>
                  <div className="form-grid">
                    <TextInput label="Name" value={selected.name} onChange={(value) => updateSelected((character) => ({ ...character, name: value }))} />
                    <ReferencePicker label="Location" kind="location" index={referenceIndex} value={selected.location_id} onChange={(value) => updateSelected((character) => ({ ...character, location_id: value }))} allowEmpty={false} />
                    <TextInput label="Knowledge refs" value={selected.knowledge.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, knowledge: commaList(value) }))} />
                    <TextInput label="Scene moods" value={selected.scene_mood_preferences.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, scene_mood_preferences: commaList(value) }))} />
                  </div>
                  <label>Personality<textarea value={selected.personality} onChange={(event) => updateSelected((character) => ({ ...character, personality: event.target.value }))} /></label>
                  <div className="checkbox-grid">
                    <label><input type="checkbox" checked={selected.visible} onChange={(event) => updateSelected((character) => ({ ...character, visible: event.target.checked }))} /> Visible</label>
                    <label><input type="checkbox" checked={selected.hidden} onChange={(event) => updateSelected((character) => ({ ...character, hidden: event.target.checked }))} /> Hidden</label>
                  </div>
                </section>

                <section className="authoring-preview-box">
                  <h3>RP Profile</h3>
                  <label>Public persona<textarea value={selected.rp_profile.public_persona} onChange={(event) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, public_persona: event.target.value } }))} /></label>
                  <label>Private self summary<textarea value={selected.rp_profile.private_self_summary ?? ""} onChange={(event) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, private_self_summary: emptyToNull(event.target.value) } }))} /></label>
                  <div className="form-grid">
                    <TextInput label="Trust expression" value={selected.rp_profile.trust_expression_style} onChange={(value) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, trust_expression_style: value } }))} />
                    <TextInput label="Conflict expression" value={selected.rp_profile.conflict_expression_style} onChange={(value) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, conflict_expression_style: value } }))} />
                    <TextInput label="Intimacy expression" value={selected.rp_profile.intimacy_expression_style} onChange={(value) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, intimacy_expression_style: value } }))} />
                    <TextInput label="Boundaries" value={selected.rp_profile.boundaries.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, rp_profile: { ...character.rp_profile, boundaries: commaList(value) } }))} />
                  </div>
                </section>

                <section className="authoring-preview-box">
                  <h3>Voice / Emotion</h3>
                  <div className="form-grid">
                    <TextInput label="Tone" value={selected.voice_profile.tone} onChange={(value) => updateSelected((character) => ({ ...character, voice_profile: { ...character.voice_profile, tone: value } }))} />
                    <TextInput label="Sentence length" value={selected.voice_profile.sentence_length} onChange={(value) => updateSelected((character) => ({ ...character, voice_profile: { ...character.voice_profile, sentence_length: value } }))} />
                    <TextInput label="Catchphrases" value={selected.voice_profile.catchphrases.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, voice_profile: { ...character.voice_profile, catchphrases: commaList(value) } }))} />
                    <TextInput label="Speech habits" value={selected.voice_profile.speech_habits.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, voice_profile: { ...character.voice_profile, speech_habits: commaList(value) } }))} />
                    <TextInput label="Default emotion" value={selected.default_emotional_state.primary_emotion} onChange={(value) => updateSelected((character) => ({ ...character, default_emotional_state: { ...character.default_emotional_state, primary_emotion: value } }))} />
                    <NumberInput label="Intensity" value={selected.default_emotional_state.intensity} onChange={(value) => updateSelected((character) => ({ ...character, default_emotional_state: { ...character.default_emotional_state, intensity: value } }))} />
                  </div>
                </section>

                <section className="authoring-preview-box">
                  <h3>Example Dialogue</h3>
                  <TextInput label="Prompt-safe refs" value={selected.example_dialogue_refs.join(", ")} onChange={(value) => updateSelected((character) => ({ ...character, example_dialogue_refs: commaList(value) }))} />
                  <ul className="compact-list">
                    {selected.example_dialogues.map((entry) => (
                      <li key={entry.id}>{entry.id}: {entry.visibility} / {entry.fact_policy}</li>
                    ))}
                  </ul>
                </section>
              </>
            ) : (
              <EmptyState title="No RP character selected." detail="Select an NPC to edit RP authoring fields." />
            )}

            <section className="authoring-preview-box">
              <h3>Character Card Import Preview</h3>
              <textarea value={importDraft} onChange={(event) => setImportDraft(event.target.value)} />
              <button type="button" onClick={() => void handleImportPreview()} disabled={isBusy}>Preview Import</button>
              {importReport && (
                <p className={importReport.ok ? "muted" : "danger-text"}>
                  {importReport.ok ? "Safe import candidate" : "Unsafe entries quarantined"}; examples {importReport.example_dialogue_candidate.lines.length}; hidden candidates {importReport.hidden_fact_candidate.length}.
                </p>
              )}
            </section>

            <section className="authoring-preview-box">
              <h3>Batch Character Import</h3>
              <p className="muted">Paste multiple JSON/YAML cards separated by --- . Preview and export create drafts only.</p>
              <textarea value={batchImportDraft} onChange={(event) => setBatchImportDraft(event.target.value)} />
              <div className="authoring-header-actions">
                <button type="button" onClick={() => void handleBatchImportPreview()} disabled={isBusy}>Preview Batch</button>
                <button type="button" onClick={() => void handleBatchApplyDraft()} disabled={isBusy || !batchImportReport}>Apply Draft</button>
                <button type="button" onClick={() => void handleBatchExportPack()} disabled={isBusy || !batchImportReport}>Export Pack</button>
              </div>
              {batchImportReport && (
                <div className="diff-summary">
                  <p>
                    Parsed {batchImportReport.parsed_count}; failed {batchImportReport.failed_count};
                    unsafe {batchImportReport.unsafe_count}; duplicates {batchImportReport.duplicate_names.join(", ") || "none"}.
                  </p>
                  <ul className="compact-list">
                    {batchImportReport.candidate_characters.map((candidate) => {
                      const name = String(candidate.name ?? "");
                      return (
                        <li key={String(candidate.id ?? name)}>
                          <label>
                            <input
                              type="checkbox"
                              checked={selectedBatchNames.includes(name)}
                              onChange={(event) => {
                                setSelectedBatchNames((current) =>
                                  event.target.checked
                                    ? Array.from(new Set([...current, name]))
                                    : current.filter((item) => item !== name)
                                );
                              }}
                            />
                            {name || String(candidate.id)}
                          </label>
                        </li>
                      );
                    })}
                  </ul>
                  {batchImportReport.unsafe_entries.length > 0 && (
                    <AuthoringPreviewCode content={JSON.stringify(batchImportReport.unsafe_entries, null, 2)} />
                  )}
                </div>
              )}
            </section>

            <AuthoringActionBar
              onPreview={() => void handlePreview()}
              onValidate={() => void handleValidate()}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <div className="template-grid">
              <label>
                Export profile
                <select
                  value={selectedExportProfileId}
                  onChange={(event) => setSelectedExportProfileId(event.target.value)}
                  disabled={isBusy}
                >
                  {exportProfiles.length === 0 && <option value="safe">Safe Export</option>}
                  {exportProfiles.map((profile) => (
                    <option key={profile.profile_id} value={profile.profile_id}>
                      {profile.name}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={() => void handleCharacterPackExport()} disabled={isBusy || !selectedNpcId}>
                Export Character Pack
              </button>
              <button type="button" onClick={() => void handleSafeExport()} disabled={isBusy || !selectedNpcId}>Export Safe Character Card</button>
            </div>
            {safeExport && <textarea readOnly value={safeExport} />}
            <PreviewResultPanel title="RP Character Validation" validation={validation} />
          </div>
        </div>
      ) : (
        <EmptyState title="No RP character graph loaded." detail="Load npcs.yaml through the authoring API to edit RP character fields." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ExampleDialogueManagerPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContent: string, validation: AuthoringValidation) => void;
}) {
  const [entries, setEntries] = useState<ExampleDialogue[]>([]);
  const [draftText, setDraftText] = useState<string>("[]");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [previewYaml, setPreviewYaml] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    if (worldId) {
      void loadExamples();
    }
  }, [worldId]);

  async function loadExamples() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchExampleDialogues(worldId);
      setEntries(response.entries);
      setDraftText(JSON.stringify(response.entries, null, 2));
      setValidation(null);
      setPreviewYaml("");
    } catch (err) {
      setEntries([]);
      setDraftText("[]");
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function parseDraft(): ExampleDialogue[] | null {
    try {
      const parsed = JSON.parse(draftText) as ExampleDialogue[];
      if (!Array.isArray(parsed)) {
        setError("Example dialogue draft must be a JSON array.");
        return null;
      }
      return parsed;
    } catch (err) {
      setError(authoringErrorMessage(err));
      return null;
    }
  }

  async function handlePreview() {
    const draft = parseDraft();
    if (!draft) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewExampleDialogues(worldId, draft);
      setValidation(response.validation);
      setPreviewYaml(response.yaml_content);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Example dialogue preview is valid." : "Example dialogue preview found validation errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    const draft = parseDraft();
    if (!draft) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateExampleDialogues(worldId, draft);
      setValidation(response.validation);
      setPreviewYaml(response.yaml_content);
      setMessage(response.validation.ok ? "Example dialogue validation passed." : "Example dialogue validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    const draft = parseDraft();
    if (!draft) {
      return;
    }
    const validationResponse = await validateExampleDialogues(worldId, draft);
    setValidation(validationResponse.validation);
    if (!validationResponse.validation.ok) {
      setMessage("Example dialogue has validation errors. Fix them before saving.");
      return;
    }
    if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await saveExampleDialogues(worldId, draft);
      setValidation(response.validation);
      setPreviewYaml(response.yaml_content);
      setEntries(response.entries);
      setDraftText(JSON.stringify(response.entries, null, 2));
      setMessage(response.saved ? "Example dialogue saved to example_dialogues.yaml." : "Example dialogue was not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Example Dialogue Manager</h2>
          <p>Manage prompt-safe style examples. Samples are never facts and never grant NPC knowledge.</p>
        </div>
        <button type="button" onClick={() => void loadExamples()} disabled={isBusy}>
          Reload
        </button>
      </div>
      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice api-disabled-notice">Example dialogue authoring requires the local authoring API.</div>
      )}
      <div className="dashboard-grid compact">
        <DashboardCard title="Examples" value={String(entries.length)}>
          <p>Only <code>prompt_safe</code> entries can reach dialogue prompts after visibility filtering.</p>
        </DashboardCard>
        <DashboardCard title="Prompt-safe" value={String(entries.filter((entry) => entry.visibility === "prompt_safe").length)}>
          <p>Unsafe, debug-only, and authoring-only examples stay out of player/narrator contexts.</p>
        </DashboardCard>
      </div>
      {entries.length > 0 ? (
        <div className="authoring-preview-box">
          {entries.slice(0, 6).map((entry) => (
            <div key={entry.id} className="timeline-event-row">
              <strong>{entry.id}</strong>
              <span className="badge">{entry.character_id}</span>
              <span className="badge">{entry.visibility}</span>
              <span className="badge">{entry.fact_policy}</span>
              <p className="muted">{entry.messages.map((item) => item.text).join(" / ")}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No example dialogue found." detail="Create a JSON draft below, then preview and save to example_dialogues.yaml." />
      )}
      <label className="field-block">
        Example dialogue JSON draft
        <textarea
          value={draftText}
          onChange={(event) => setDraftText(event.target.value)}
          spellCheck={false}
          disabled={isBusy}
        />
      </label>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>
          Preview
        </button>
        <button type="button" onClick={() => void handleValidate()} disabled={isBusy}>
          Validate
        </button>
        <button type="button" onClick={() => void handleSave()} disabled={isBusy}>
          Save Example Dialogue
        </button>
      </div>
      <PreviewResultPanel title="Example Dialogue Validation" validation={validation} />
      {previewYaml && (
        <details className="authoring-preview-box">
          <summary>Generated example_dialogues.yaml</summary>
          <AuthoringPreviewCode content={previewYaml} />
        </details>
      )}
      <SuccessPanel message={message} />
      <ErrorPanel message={error} />
    </section>
  );
}

function MapEditorPanel({
  worldId,
  authoringDisabled
}: {
  worldId: string;
  authoringDisabled: boolean;
}) {
  const [graph, setGraph] = useState<MapVisualGraph | null>(null);
  const [savedGraphJson, setSavedGraphJson] = useState<string>("");
  const [selectedNodeId, setSelectedNodeId] = useState<string>("");
  const [selectedEdgeIndex, setSelectedEdgeIndex] = useState<number>(-1);
  const [newEdge, setNewEdge] = useState<MapVisualEdge>({
    source_location_id: "",
    target_location_id: "",
    edge_type: "exit",
    label: "path",
    visibility: "public",
    travel_cost: 1,
    discovery_rules: []
  });
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [previewYaml, setPreviewYaml] = useState<string>("");
  const [mapDiffSummary, setMapDiffSummary] = useState<AuthoringDiffSummary | null>(null);
  const [draggingNodeId, setDraggingNodeId] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const referenceIndex = useReferenceIndex(worldId);

  useEffect(() => {
    if (worldId) {
      void loadMap();
    }
  }, [worldId]);

  const selectedNode = graph?.nodes.find((node) => node.location_id === selectedNodeId) ?? graph?.nodes[0] ?? null;
  const selectedEdge = graph && selectedEdgeIndex >= 0 ? graph.edges[selectedEdgeIndex] ?? null : null;
  const isDirty = graph ? JSON.stringify(graph) !== savedGraphJson : false;

  async function loadMap() {
    setIsBusy(true);
    setError("");
    setMessage("");
    setPreviewYaml("");
    try {
      const response = await fetchAuthoringMap(worldId);
      setGraph(response.graph);
      setSavedGraphJson(JSON.stringify(response.graph));
      setSelectedNodeId(response.graph.nodes[0]?.location_id ?? "");
      setSelectedEdgeIndex(response.graph.edges.length > 0 ? 0 : -1);
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePreviewMap() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewAuthoringMap(worldId, graph);
      setValidation(response.validation);
      setPreviewYaml(response.yaml_content);
      setMapDiffSummary(response.diff_summary ?? null);
      setMessage(response.validation.ok ? "Map preview is valid." : "Map preview found validation errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidateMap() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateAuthoringMap(worldId, graph);
      setValidation(response);
      setMessage(response.ok ? "Map validation passed." : "Map validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveMap() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateAuthoringMap(worldId, graph);
      setValidation(validationResponse);
      if (!validationResponse.ok) {
        setError("Validation errors block saving this map.");
        return;
      }
      if (validationResponse.warnings.length > 0) {
        const confirmedWarnings = confirmDangerousAction("Map validation has warnings. Save this local map anyway?");
        if (!confirmedWarnings) {
          return;
        }
      }
      const confirmed = confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges);
      if (!confirmed) {
        return;
      }
      const response = await saveAuthoringMap(worldId, graph, validationResponse.warnings.length > 0);
      setGraph(response.graph);
      setSavedGraphJson(JSON.stringify(response.graph));
      setValidation(response.validation);
      setPreviewYaml("");
      setMapDiffSummary(null);
      setMessage(response.confirmation_required ? "Saved with warnings." : "Map saved and validated.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateNode(locationId: string, updates: Partial<MapVisualNode>) {
    setGraph((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        nodes: current.nodes.map((node) =>
          node.location_id === locationId ? { ...node, ...updates } : node
        )
      };
    });
    setPreviewYaml("");
    setMapDiffSummary(null);
  }

  function updateEdge(index: number, updates: Partial<MapVisualEdge>) {
    setGraph((current) => {
      if (!current) {
        return current;
      }
      return {
        ...current,
        edges: current.edges.map((edge, edgeIndex) =>
          edgeIndex === index ? { ...edge, ...updates } : edge
        )
      };
    });
    setPreviewYaml("");
    setMapDiffSummary(null);
  }

  function addEdge() {
    if (!graph || !newEdge.source_location_id || !newEdge.target_location_id || !newEdge.label.trim()) {
      setError("Choose source, target, and edge label before adding an exit.");
      return;
    }
    setError("");
    setGraph({
      ...graph,
      edges: [...graph.edges, { ...newEdge, label: newEdge.label.trim() }]
    });
    setSelectedEdgeIndex(graph.edges.length);
    setPreviewYaml("");
  }

  function deleteEdge(index: number) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      edges: graph.edges.filter((_edge, edgeIndex) => edgeIndex !== index)
    });
    setSelectedEdgeIndex(-1);
    setPreviewYaml("");
  }

  function addNode() {
    if (!graph) {
      return;
    }
    const nextIndex = graph.nodes.length + 1;
    const locationId = `new_location_${nextIndex}`;
    const node: MapVisualNode = {
      id: locationId,
      location_id: locationId,
      name: `New Location ${nextIndex}`,
      x: nextIndex * 80,
      y: nextIndex * 40,
      region_id: graph.regions[0]?.id ?? null,
      layer_id: graph.layers[0]?.id ?? null,
      tags: [],
      visibility: "public"
    };
    setGraph({ ...graph, nodes: [...graph.nodes, node] });
    setSelectedNodeId(locationId);
    setPreviewYaml("");
  }

  function deleteNode(locationId: string) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      nodes: graph.nodes.filter((node) => node.location_id !== locationId),
      edges: graph.edges.filter(
        (edge) => edge.source_location_id !== locationId && edge.target_location_id !== locationId
      )
    });
    setSelectedNodeId(graph.nodes.find((node) => node.location_id !== locationId)?.location_id ?? "");
    setSelectedEdgeIndex(-1);
    setPreviewYaml("");
  }

  function addRegion() {
    if (!graph) {
      return;
    }
    const id = `region_${graph.regions.length + 1}`;
    setGraph({ ...graph, regions: [...graph.regions, { id, name: id.replace("_", " ") }] });
  }

  function addLayer() {
    if (!graph) {
      return;
    }
    const id = `layer_${graph.layers.length + 1}`;
    setGraph({ ...graph, layers: [...graph.layers, { id, name: id.replace("_", " "), order: graph.layers.length }] });
  }

  if (authoringDisabled) {
    return (
      <section className="studio-section">
        <h2>Map Editor</h2>
        <EmptyState title="Authoring unavailable." detail="Enable the local authoring API to load the map editor." />
      </section>
    );
  }

  return (
    <section className="map-editor-panel">
      <div className="authoring-pane-header">
        <div>
          <h2>Map Editor</h2>
          <p className="muted">Visual authoring data for locations and exits. Player map visibility stays filtered by backend rules.</p>
        </div>
        {isDirty && <span className="dirty-badge">Unsaved map changes</span>}
      </div>

      <DirtyStateBanner dirty={isDirty} label="Map graph edits are local until Save Map writes locations.yaml." />

      <div className="map-editor-actions">
        <button type="button" onClick={() => void loadMap()} disabled={isBusy}>
          Reload Map
        </button>
        <AuthoringActionBar
          onPreview={() => void handlePreviewMap()}
          onValidate={() => void handleValidateMap()}
          onSave={() => void handleSaveMap()}
          disabled={!graph || isBusy}
          saveLabel="Save Map"
        />
        <button
          type="button"
          onClick={() => {
            if (savedGraphJson) {
              const restored = JSON.parse(savedGraphJson) as MapVisualGraph;
              setGraph(restored);
              setSelectedNodeId(restored.nodes[0]?.location_id ?? "");
              setPreviewYaml("");
              setMessage("Discarded map edits.");
            }
          }}
          disabled={!isDirty || isBusy}
        >
          Discard Map
        </button>
      </div>

      {graph ? (
        <div className="map-editor-grid">
          <MapEditorSvg
            graph={graph}
            selectedNodeId={selectedNode?.location_id ?? ""}
            selectedEdgeIndex={selectedEdgeIndex}
            onSelectNode={setSelectedNodeId}
            onSelectEdge={setSelectedEdgeIndex}
            draggingNodeId={draggingNodeId}
            onDragStart={setDraggingNodeId}
            onDragEnd={() => setDraggingNodeId("")}
            onMoveNode={(locationId, x, y) => updateNode(locationId, { x, y })}
          />

          <section className="map-editor-form">
            <h3>Node</h3>
            <div className="button-row">
              <button type="button" onClick={addNode} disabled={isBusy}>Add Location</button>
              <button type="button" className="danger-button" onClick={() => selectedNode && deleteNode(selectedNode.location_id)} disabled={!selectedNode || isBusy}>
                Delete Location
              </button>
            </div>
            {selectedNode ? (
              <div className="form-grid">
                <label>
                  Label
                  <input
                    value={selectedNode.name}
                    onChange={(event) => updateNode(selectedNode.location_id, { name: event.target.value })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Id
                  <input value={selectedNode.location_id} disabled />
                </label>
                <label>
                  X
                  <input
                    type="number"
                    value={selectedNode.x}
                    onChange={(event) => updateNode(selectedNode.location_id, { x: Number(event.target.value) })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Y
                  <input
                    type="number"
                    value={selectedNode.y}
                    onChange={(event) => updateNode(selectedNode.location_id, { y: Number(event.target.value) })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Region
                  <select
                    value={selectedNode.region_id ?? ""}
                    onChange={(event) => updateNode(selectedNode.location_id, { region_id: event.target.value || null })}
                    disabled={isBusy}
                  >
                    <option value="">None</option>
                    {graph.regions.map((region) => <option key={region.id} value={region.id}>{region.name || region.id}</option>)}
                  </select>
                </label>
                <label>
                  Layer
                  <select
                    value={selectedNode.layer_id ?? ""}
                    onChange={(event) => updateNode(selectedNode.location_id, { layer_id: event.target.value || null })}
                    disabled={isBusy}
                  >
                    <option value="">Default</option>
                    {graph.layers.map((layer) => <option key={layer.id} value={layer.id}>{layer.name || layer.id}</option>)}
                  </select>
                </label>
                <label>
                  Tags
                  <input
                    value={selectedNode.tags.join(", ")}
                    onChange={(event) => updateNode(selectedNode.location_id, { tags: splitCsv(event.target.value) })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Visibility
                  <select
                    value={selectedNode.visibility}
                    onChange={(event) => updateNode(selectedNode.location_id, { visibility: event.target.value as MapVisibility })}
                    disabled={isBusy}
                  >
                    {MAP_VISIBILITIES.map((visibility) => (
                      <option key={visibility} value={visibility}>
                        {visibility}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="full-width">
                  <HiddenContentBadge visibility={selectedNode.visibility} />
                </div>
                <div className="map-nudge-controls">
                  <button type="button" onClick={() => updateNode(selectedNode.location_id, { y: selectedNode.y - 20 })}>Up</button>
                  <button type="button" onClick={() => updateNode(selectedNode.location_id, { x: selectedNode.x - 20 })}>Left</button>
                  <button type="button" onClick={() => updateNode(selectedNode.location_id, { x: selectedNode.x + 20 })}>Right</button>
                  <button type="button" onClick={() => updateNode(selectedNode.location_id, { y: selectedNode.y + 20 })}>Down</button>
                </div>
              </div>
            ) : (
              <EmptyState title="No node selected." />
            )}
          </section>

          <section className="map-editor-form">
            <h3>Edges</h3>
            <div className="map-summary-row">
              <span>Regions {graph.regions.length}</span>
              <span>Layers {graph.layers.length}</span>
              <span>Hidden paths {graph.edges.filter((edge) => edge.edge_type === "hidden" || edge.visibility === "hidden").length}</span>
              <span>Locked {graph.edges.filter((edge) => edge.edge_type === "locked").length}</span>
            </div>
            <div className="button-row">
              <button type="button" onClick={addRegion} disabled={isBusy}>Add Region</button>
              <button type="button" onClick={addLayer} disabled={isBusy}>Add Layer</button>
            </div>
            <div className="edge-list">
              {graph.edges.map((edge, index) => (
                <button
                  type="button"
                  key={`${edge.source_location_id}-${edge.label}-${index}`}
                  className={`edge-row ${selectedEdgeIndex === index ? "selected" : ""}`}
                  onClick={() => setSelectedEdgeIndex(index)}
                >
                  {edge.source_location_id} -{edge.label}-&gt; {edge.target_location_id}
                  <span>{edge.edge_type}</span>
                </button>
              ))}
            </div>

            {selectedEdge && (
              <div className="form-grid">
                <ReferencePicker label="Source" kind="location" index={referenceIndex} value={selectedEdge.source_location_id} onChange={(value) => updateEdge(selectedEdgeIndex, { source_location_id: value })} allowEmpty={false} disabled={isBusy} />
                <ReferencePicker label="Target" kind="location" index={referenceIndex} value={selectedEdge.target_location_id} onChange={(value) => updateEdge(selectedEdgeIndex, { target_location_id: value })} allowEmpty={false} disabled={isBusy} />
                <label>
                  Label
                  <input
                    value={selectedEdge.label}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { label: event.target.value })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Type
                  <select
                    value={selectedEdge.edge_type}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { edge_type: event.target.value as MapVisualEdgeType })}
                    disabled={isBusy}
                  >
                    {MAP_EDGE_TYPES.map((edgeType) => (
                      <option key={edgeType} value={edgeType}>
                        {edgeType}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Visibility
                  <select
                    value={selectedEdge.visibility}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { visibility: event.target.value as MapVisibility })}
                    disabled={isBusy}
                  >
                    {MAP_VISIBILITIES.map((visibility) => <option key={visibility} value={visibility}>{visibility}</option>)}
                  </select>
                </label>
                <label>
                  Travel cost
                  <input
                    type="number"
                    min={0}
                    value={selectedEdge.travel_cost}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { travel_cost: Number(event.target.value) })}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Unlock / condition
                  <input
                    value={selectedEdge.unlock_condition ?? ""}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { unlock_condition: event.target.value || null })}
                    disabled={isBusy}
                  />
                </label>
                <label className="full-width">
                  Discovery rules
                  <input
                    value={(selectedEdge.discovery_rules ?? []).join(", ")}
                    onChange={(event) => updateEdge(selectedEdgeIndex, { discovery_rules: splitCsv(event.target.value) })}
                    disabled={isBusy}
                  />
                </label>
                <div className="full-width">
                  <HiddenContentBadge visibility={selectedEdge.visibility} />
                </div>
                <button type="button" className="danger-button" onClick={() => deleteEdge(selectedEdgeIndex)} disabled={isBusy}>
                  Delete Edge
                </button>
              </div>
            )}

            <h4>Add Exit</h4>
            <div className="form-grid">
              <ReferencePicker label="Source" kind="location" index={referenceIndex} value={newEdge.source_location_id} onChange={(value) => setNewEdge({ ...newEdge, source_location_id: value })} />
              <ReferencePicker label="Target" kind="location" index={referenceIndex} value={newEdge.target_location_id} onChange={(value) => setNewEdge({ ...newEdge, target_location_id: value })} />
              <label>
                Label
                <input value={newEdge.label} onChange={(event) => setNewEdge({ ...newEdge, label: event.target.value })} />
              </label>
              <label>
                Type
                <select
                  value={newEdge.edge_type}
                  onChange={(event) => setNewEdge({ ...newEdge, edge_type: event.target.value as MapVisualEdgeType })}
                >
                  {MAP_EDGE_TYPES.map((edgeType) => (
                    <option key={edgeType} value={edgeType}>
                      {edgeType}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Visibility
                <select
                  value={newEdge.visibility}
                  onChange={(event) => setNewEdge({ ...newEdge, visibility: event.target.value as MapVisibility })}
                >
                  {MAP_VISIBILITIES.map((visibility) => <option key={visibility} value={visibility}>{visibility}</option>)}
                </select>
              </label>
              <label>
                Travel cost
                <input
                  type="number"
                  min={0}
                  value={newEdge.travel_cost}
                  onChange={(event) => setNewEdge({ ...newEdge, travel_cost: Number(event.target.value) })}
                />
              </label>
              <button type="button" onClick={addEdge} disabled={isBusy}>
                Add Edge
              </button>
            </div>
          </section>
        </div>
      ) : (
        <EmptyState title="Map unavailable." detail="Load a world with locations.yaml to edit the visual map." />
      )}

      <PreviewResultPanel title="Map Validation / Preview" validation={validation} previewContent={previewYaml} />
      {mapDiffSummary && (
        <section className="debug-group">
          <h3>Diff Preview</h3>
          <ItemList
            emptyText="No map entity changes."
            items={[
              ...mapDiffSummary.added_ids.map((id: string) => <span key={`add-${id}`}>added {id}</span>),
              ...mapDiffSummary.removed_ids.map((id: string) => <span key={`remove-${id}`}>removed {id}</span>),
              ...mapDiffSummary.changed_ids.map((id: string) => <span key={`change-${id}`}>changed {id}</span>)
            ]}
          />
        </section>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function MapEditorSvg({
  graph,
  selectedNodeId,
  selectedEdgeIndex,
  onSelectNode,
  onSelectEdge,
  draggingNodeId,
  onDragStart,
  onDragEnd,
  onMoveNode
}: {
  graph: MapVisualGraph;
  selectedNodeId: string;
  selectedEdgeIndex: number;
  onSelectNode: (locationId: string) => void;
  onSelectEdge: (edgeIndex: number) => void;
  draggingNodeId: string;
  onDragStart: (locationId: string) => void;
  onDragEnd: () => void;
  onMoveNode: (locationId: string, x: number, y: number) => void;
}) {
  const positions = mapNodePositions(graph.nodes);
  function handlePointerMove(event: PointerEvent<SVGSVGElement>) {
    if (!draggingNodeId) {
      return;
    }
    const svg = event.currentTarget;
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;
    const transformed = point.matrixTransform(svg.getScreenCTM()?.inverse());
    const raw = mapSvgToNodeCoordinates(graph.nodes, transformed.x, transformed.y);
    onMoveNode(draggingNodeId, Math.round(raw.x), Math.round(raw.y));
  }
  return (
    <svg
      className="map-editor-svg"
      viewBox="0 0 520 320"
      role="img"
      aria-label="Visual map editor"
      onPointerMove={handlePointerMove}
      onPointerUp={onDragEnd}
      onPointerLeave={onDragEnd}
    >
      {graph.edges.map((edge, index) => {
        const source = positions[edge.source_location_id];
        const target = positions[edge.target_location_id];
        if (!source || !target) {
          return null;
        }
        const midX = (source.x + target.x) / 2;
        const midY = (source.y + target.y) / 2;
        return (
          <g key={`${edge.source_location_id}-${edge.label}-${index}`} onClick={() => onSelectEdge(index)}>
            <line
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              className={`map-edge ${edge.visibility} ${edge.edge_type} ${selectedEdgeIndex === index ? "selected" : ""}`}
            />
            <text x={midX} y={midY - 6} textAnchor="middle" className="map-edge-label">
              {edge.label}
            </text>
          </g>
        );
      })}
      {graph.nodes.map((node) => {
        const position = positions[node.location_id];
        return (
          <g
            key={node.location_id}
            onPointerDown={(event) => {
              event.preventDefault();
              onSelectNode(node.location_id);
              onDragStart(node.location_id);
            }}
          >
            <circle
              cx={position.x}
              cy={position.y}
              r={selectedNodeId === node.location_id ? 16 : 13}
              className={`map-node ${node.visibility} ${selectedNodeId === node.location_id ? "selected" : ""}`}
            />
            <text x={position.x} y={position.y + 28} textAnchor="middle">
              {shortLabel(node.name || node.location_id)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function mapSvgToNodeCoordinates(nodes: MapVisualNode[], svgX: number, svgY: number): { x: number; y: number } {
  if (nodes.length === 0) {
    return { x: svgX, y: svgY };
  }
  const xs = nodes.map((node) => node.x);
  const ys = nodes.map((node) => node.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(maxX - minX, 1);
  const height = Math.max(maxY - minY, 1);
  return {
    x: minX + ((svgX - 50) / 420) * width,
    y: minY + ((svgY - 50) / 220) * height
  };
}

function mapNodePositions(nodes: MapVisualNode[]): Record<string, { x: number; y: number }> {
  if (nodes.length === 0) {
    return {};
  }
  const xs = nodes.map((node) => node.x);
  const ys = nodes.map((node) => node.y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const width = Math.max(maxX - minX, 1);
  const height = Math.max(maxY - minY, 1);
  return Object.fromEntries(
    nodes.map((node) => [
      node.location_id,
      {
        x: 50 + ((node.x - minX) / width) * 420,
        y: 50 + ((node.y - minY) / height) * 220
      }
    ])
  );
}

function splitCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function ScenarioRegressionAuthoringPanel({ selectedWorldId }: { selectedWorldId: string }) {
  const [scenarios, setScenarios] = useState<ScenarioRegressionCase[]>([]);
  const [scenario, setScenario] = useState<ScenarioRegressionCase>(() => defaultScenarioDraft(selectedWorldId));
  const [expectedQuestText, setExpectedQuestText] = useState<string>("{}");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [preview, setPreview] = useState<ScenarioAuthoringPreviewResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadScenarios();
  }, []);

  useEffect(() => {
    setScenario((current) => ({ ...current, world_id: current.world_id || selectedWorldId }));
  }, [selectedWorldId]);

  async function loadScenarios() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchAuthoringScenarios();
      setScenarios(response.scenarios);
      if (response.scenarios.length > 0) {
        setScenario(response.scenarios[0]);
        setExpectedQuestText(JSON.stringify(response.scenarios[0].expected_quest_states, null, 2));
      }
    } catch (err) {
      setScenarios([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateScenario(updater: (current: ScenarioRegressionCase) => ScenarioRegressionCase) {
    setScenario((current) => updater(current));
    setPreview(null);
    setValidation(null);
  }

  function scenarioWithQuestStates(): ScenarioRegressionCase | null {
    try {
      const parsed = JSON.parse(expectedQuestText || "{}") as Record<string, string>;
      return { ...scenario, expected_quest_states: parsed };
    } catch {
      setError("Expected quest states must be valid JSON, for example {\"quest_id\":\"active\"}.");
      return null;
    }
  }

  async function handlePreviewScenario() {
    const next = scenarioWithQuestStates();
    if (!next) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewAuthoringScenario(next);
      setPreview(response);
      setValidation(response.validation);
      setMessage(response.validation.ok ? "Scenario preview passed. No file was written." : "Scenario preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidateScenario() {
    const next = scenarioWithQuestStates();
    if (!next) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateAuthoringScenario(next);
      setPreview(response);
      setValidation(response.validation);
      setMessage(response.validation.ok ? "Scenario validation passed." : "Scenario validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveScenario() {
    const next = scenarioWithQuestStates();
    if (!next) {
      return;
    }
    if (!confirmDangerousAction(`Save local scenario '${next.id}' after validation? This writes a local scenario file.`)) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await saveAuthoringScenario(next);
      setPreview(response);
      setValidation(response.validation);
      if (response.writes_to_disk) {
        setMessage("Scenario saved after validation.");
        await loadScenarios();
      } else {
        setMessage("Scenario was not saved because validation failed.");
      }
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Scenario Regression Authoring</h2>
          <p className="muted">Create local scenario cases for quest paths, hidden leak probes, and save/load checks.</p>
        </div>
        <button type="button" onClick={() => void loadScenarios()} disabled={isBusy}>
          Refresh Scenarios
        </button>
      </div>

      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice api-disabled-notice">Scenario authoring requires the local authoring API.</div>
      )}

      <div className="template-grid">
        <label>
          Existing scenario
          <select
            value={scenarios.find((item) => item.id === scenario.id)?.id ?? ""}
            onChange={(event) => {
              const selected = scenarios.find((item) => item.id === event.target.value);
              if (selected) {
                setScenario(selected);
                setExpectedQuestText(JSON.stringify(selected.expected_quest_states, null, 2));
                setPreview(null);
                setValidation(null);
              }
            }}
            disabled={isBusy || scenarios.length === 0}
          >
            <option value="">New scenario</option>
            {scenarios.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => {
            const draft = defaultScenarioDraft(selectedWorldId);
            setScenario(draft);
            setExpectedQuestText("{}");
            setPreview(null);
            setValidation(null);
          }}
          disabled={isBusy}
        >
          New Draft
        </button>
        <span className="badge">{preview?.writes_to_disk ? "saved" : "preview only"}</span>
      </div>

      <div className="template-variable-grid">
        <label>
          Scenario id
          <input value={scenario.id} onChange={(event) => updateScenario((current) => ({ ...current, id: event.target.value }))} disabled={isBusy} />
        </label>
        <label>
          Name
          <input value={scenario.name} onChange={(event) => updateScenario((current) => ({ ...current, name: event.target.value }))} disabled={isBusy} />
        </label>
        <label>
          World
          <input value={scenario.world_id} onChange={(event) => updateScenario((current) => ({ ...current, world_id: event.target.value }))} disabled={isBusy} />
        </label>
        <label>
          Max turns
          <input
            type="number"
            min={0}
            value={scenario.max_turns}
            onChange={(event) => updateScenario((current) => ({ ...current, max_turns: Number(event.target.value) }))}
            disabled={isBusy}
          />
        </label>
        <label>
          Tags
          <input value={scenario.tags.join(", ")} onChange={(event) => updateScenario((current) => ({ ...current, tags: splitCsv(event.target.value) }))} disabled={isBusy} />
        </label>
        <label>
          Expected visible facts
          <input value={scenario.expected_visible_facts.join(", ")} onChange={(event) => updateScenario((current) => ({ ...current, expected_visible_facts: splitCsv(event.target.value) }))} disabled={isBusy} />
        </label>
        <label>
          Forbidden visible facts
          <input value={scenario.forbidden_visible_facts.join(", ")} onChange={(event) => updateScenario((current) => ({ ...current, forbidden_visible_facts: splitCsv(event.target.value) }))} disabled={isBusy} />
        </label>
        <label>
          Expected inventory
          <input value={scenario.expected_inventory.join(", ")} onChange={(event) => updateScenario((current) => ({ ...current, expected_inventory: splitCsv(event.target.value) }))} disabled={isBusy} />
        </label>
      </div>

      <label className="full-width-field">
        Description
        <textarea value={scenario.description} onChange={(event) => updateScenario((current) => ({ ...current, description: event.target.value }))} disabled={isBusy} />
      </label>
      <label className="full-width-field">
        Input sequence
        <textarea
          value={scenario.input_sequence.join("\n")}
          onChange={(event) => updateScenario((current) => ({ ...current, input_sequence: event.target.value.split("\n").map((line) => line.trim()).filter(Boolean) }))}
          disabled={isBusy}
        />
      </label>
      <label className="full-width-field">
        Expected quest states JSON
        <textarea value={expectedQuestText} onChange={(event) => setExpectedQuestText(event.target.value)} disabled={isBusy} />
      </label>

      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreviewScenario()} disabled={isBusy}>Preview Scenario</button>
        <button type="button" onClick={() => void handleValidateScenario()} disabled={isBusy}>Validate Scenario</button>
        <button type="button" onClick={() => void handleSaveScenario()} disabled={isBusy}>Save Scenario</button>
      </div>

      {validation && (
        <ValidationPanel
          validation={validation}
          onSelectIssue={() => undefined}
        />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function defaultScenarioDraft(worldId: string): ScenarioRegressionCase {
  return {
    id: "new_scenario",
    world_id: worldId || "mist_valley",
    name: "New Scenario",
    description: "",
    initial_save: null,
    input_sequence: ["observe"],
    expected_visible_facts: [],
    forbidden_visible_facts: [],
    expected_quest_states: {},
    expected_inventory: [],
    max_turns: 5,
    tags: []
  };
}

const TEMPLATE_WIZARD_TYPES: TemplateWizardType[] = [
  "world",
  "location_cluster",
  "questline",
  "npc_set",
  "character_pack",
  "dialogue_scene",
  "group_rp_scene",
  "faction_conflict",
  "mystery_case"
];

function TemplateWizardPanel({ worldId }: { worldId: string }) {
  const [draft, setDraft] = useState<TemplateWizardDraft>(() => defaultTemplateWizardDraft(worldId));
  const [variableText, setVariableText] = useState<string>("location_id=village_square\nnpc_id=harlan");
  const [preview, setPreview] = useState<TemplateWizardPreviewResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    setDraft((current) => ({ ...current, target_world_id: current.template_type === "world" ? null : worldId }));
  }, [worldId]);

  function buildDraft(): TemplateWizardDraft {
    return {
      ...draft,
      variables: parseKeyValueLines(variableText),
      target_world_id: draft.template_type === "world" ? null : worldId
    };
  }

  async function handlePreview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewTemplateWizard(buildDraft());
      setPreview(response);
      setMessage(response.validation?.ok ? "Wizard preview generated without writing files." : "Wizard preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateTemplateWizard(buildDraft());
      setPreview(response);
      setMessage(response.validation?.ok ? "Wizard draft validates." : "Wizard draft needs changes.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApply() {
    const nextDraft = buildDraft();
    const action = nextDraft.save_as_template ? "save this wizard output as a local template" : "apply this wizard output to the local world pack";
    if (!confirmDangerousAction(`Validate and ${action}?`)) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyTemplateWizard(nextDraft, true, true);
      setPreview(response);
      setMessage(response.saved_template ? "Wizard template saved." : response.applied ? "Wizard output applied after validation." : "Wizard apply was blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Template Wizard</h2>
          <p className="muted">Step through type, variables, preview, validation, and explicit save/apply.</p>
        </div>
        <span className="badge">{draft.current_step}</span>
      </div>
      <div className="template-grid">
        <label>
          Type
          <select
            value={draft.template_type}
            onChange={(event) => {
              const nextType = event.target.value as TemplateWizardType;
              setDraft({ ...draft, template_type: nextType, target_world_id: nextType === "world" ? null : worldId, current_step: "fill_variables" });
              setPreview(null);
            }}
            disabled={isBusy}
          >
            {TEMPLATE_WIZARD_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <TextInput label="Draft id" value={draft.id} onChange={(value) => setDraft({ ...draft, id: value })} />
        <TextInput label="Name" value={draft.name} onChange={(value) => setDraft({ ...draft, name: value })} />
        <label>
          Target world
          <input value={draft.template_type === "world" ? "(new world)" : worldId} disabled />
        </label>
      </div>
      <label className="full-width-field">
        Variables
        <textarea value={variableText} onChange={(event) => setVariableText(event.target.value)} disabled={isBusy} />
      </label>
      <label>
        <input type="checkbox" checked={draft.save_as_template} onChange={(event) => setDraft({ ...draft, save_as_template: event.target.checked })} />
        Save as reusable local template
      </label>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>Preview</button>
        <button type="button" onClick={() => void handleValidate()} disabled={isBusy}>Validate</button>
        <button type="button" onClick={() => void handleApply()} disabled={isBusy}>Save / Apply</button>
      </div>
      {preview?.validation && <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />}
      {preview && (
        <div className="template-preview">
          <h3>Generated Content</h3>
          {preview.generated_files.map((file) => (
            <details key={file.file_name} open>
              <summary>{file.file_name}</summary>
              <AuthoringPreviewCode content={file.content} />
            </details>
          ))}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function BatchLorebookClassificationPanel({ worldId }: { worldId: string }) {
  const [draftText, setDraftText] = useState<string>("entries:\n  - key: village flavor\n    content: Rain changes the village songs.");
  const [filter, setFilter] = useState<"all" | "unsafe" | "hidden" | "flavor">("all");
  const [report, setReport] = useState<BatchLorebookClassificationReport | null>(null);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  function lorebookTexts(): string[] {
    return draftText.split(/\n---+\n/g).map((value) => value.trim()).filter(Boolean);
  }

  async function handlePreview() {
    const texts = lorebookTexts();
    if (!texts.length) {
      setMessage("Paste one or more lorebooks separated by ---.");
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await previewBatchLorebookClassification(worldId, texts);
      setReport(response);
      setSelectedKeys(response.structured_fact_candidates.map((entry) => String(entry.key ?? "")));
      setMessage(`Classified ${response.total_entries} lorebook entries.`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApplyDraft() {
    const texts = lorebookTexts();
    setIsBusy(true);
    setError("");
    try {
      const response = await applyBatchLorebookClassificationDraft(worldId, texts, selectedKeys);
      setReport(response);
      setMessage(response.validation?.ok ? "Lorebook draft validates. It was not written to facts.yaml." : "Lorebook draft has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const visibleEntries = report ? batchLorebookVisibleEntries(report, filter) : [];
  return (
    <section className="authoring-preview-box">
      <h3>Batch Lorebook Classification</h3>
      <p className="muted">Classify local lorebook/world-info entries into flavor, fact candidates, hidden candidates, and unsafe entries.</p>
      <textarea value={draftText} onChange={(event) => setDraftText(event.target.value)} disabled={isBusy} />
      <div className="template-grid">
        <label>
          Filter
          <select value={filter} onChange={(event) => setFilter(event.target.value as typeof filter)}>
            <option value="all">all</option>
            <option value="flavor">flavor</option>
            <option value="hidden">hidden</option>
            <option value="unsafe">unsafe</option>
          </select>
        </label>
      </div>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>Preview</button>
        <button type="button" onClick={() => void handleApplyDraft()} disabled={isBusy || !report}>Apply Draft</button>
      </div>
      {report && (
        <div className="diff-summary">
          <p>
            Entries {report.total_entries}; flavor {report.flavor_lore.length};
            structured {report.structured_fact_candidates.length}; hidden {report.hidden_fact_candidates.length};
            unsafe {report.unsafe_entries.length}; duplicates {report.duplicate_keys.join(", ") || "none"}.
          </p>
          <ul className="compact-list">
            {visibleEntries.map((entry) => {
              const key = String(entry.key ?? entry.source_name ?? entry.safe_summary ?? Math.random());
              const selectable = "key" in entry && key;
              return (
                <li key={key}>
                  {selectable && (
                    <input
                      type="checkbox"
                      checked={selectedKeys.includes(key)}
                      onChange={(event) =>
                        setSelectedKeys((current) =>
                          event.target.checked
                            ? Array.from(new Set([...current, key]))
                            : current.filter((item) => item !== key)
                        )
                      }
                    />
                  )}
                  <strong>{key}</strong> {String(entry.safe_summary ?? entry.reason ?? "")}
                </li>
              );
            })}
          </ul>
          {report.validation && <ValidationPanel validation={report.validation} onSelectIssue={() => undefined} />}
          {report.yaml_draft && <AuthoringPreviewCode content={report.yaml_draft} />}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} compact />
    </section>
  );
}

function batchLorebookVisibleEntries(
  report: BatchLorebookClassificationReport,
  filter: "all" | "unsafe" | "hidden" | "flavor"
): Record<string, unknown>[] {
  if (filter === "unsafe") return report.unsafe_entries;
  if (filter === "hidden") return report.hidden_fact_candidates;
  if (filter === "flavor") return report.flavor_lore;
  return [
    ...report.flavor_lore,
    ...report.structured_fact_candidates,
    ...report.hidden_fact_candidates,
    ...report.unsafe_entries
  ];
}

function ScriptPackageBuilderPanel({ worldId }: { worldId: string }) {
  const [packageId, setPackageId] = useState("local_script_pack");
  const [name, setName] = useState("Local Script Pack");
  const [quests, setQuests] = useState("find_the_old_road");
  const [characters, setCharacters] = useState("elder_mara");
  const [templates, setTemplates] = useState("opening_scene");
  const [scenarios, setScenarios] = useState("intro_regression");
  const [dependencies, setDependencies] = useState(worldId);
  const [conflicts, setConflicts] = useState("");
  const [filePath, setFilePath] = useState("beats/opening.yaml");
  const [fileContent, setFileContent] = useState("beats:\n  - id: opening\n    summary: Safe opening beat.");
  const [report, setReport] = useState<ScriptPackageBuildReport | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  function buildRequest(confirmApply = false): ScriptPackageBuildRequest {
    const deps = parseCommaList(dependencies);
    return {
      manifest: {
        package_id: packageId,
        name,
        version: "1.0",
        target_engine_version: "1.4",
        target_schema_version: "1.0",
        included_worlds: [worldId],
        included_quests: parseCommaList(quests),
        included_characters: parseCommaList(characters),
        included_templates: parseCommaList(templates),
        included_scenarios: parseCommaList(scenarios),
        included_quality_profile: "default_safe",
        dependencies: deps,
        conflicts: parseCommaList(conflicts),
        checksums: {},
        normal_manifest: true
      },
      files: [{ path: filePath, content: fileContent, hidden: filePath.toLowerCase().includes("hidden") }],
      available_dependency_ids: [worldId, ...deps],
      packages_root: "packages",
      confirm_apply: confirmApply,
      normal_report: true
    };
  }

  async function runAction(action: "dry-run" | "validate" | "build" | "export") {
    if (action === "build" && !confirmDangerousAction("Build this local script package artifact after validation?")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const request = buildRequest(action === "build");
      const response =
        action === "dry-run"
          ? await dryRunScriptPackageBuild(request)
          : action === "validate"
            ? await validateScriptPackage(request)
            : action === "build"
              ? await buildScriptPackage(request)
              : await exportScriptPackage(request);
      setReport(response);
      setMessage(
        action === "export" && response.archive_file_name
          ? `Export ready: ${response.archive_file_name}`
          : response.applied
            ? "Script package built locally."
            : "Script package report ready."
      );
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="authoring-card">
      <div className="section-heading">
        <div>
          <h3>Script Package Builder</h3>
          <p>Build local structured script packages. Executable code and sensitive files are rejected.</p>
        </div>
        <div className="button-row">
          <button onClick={() => void runAction("dry-run")} disabled={isBusy}>Dry-run</button>
          <button onClick={() => void runAction("validate")} disabled={isBusy}>Validate</button>
          <button onClick={() => void runAction("build")} disabled={isBusy}>Build</button>
          <button onClick={() => void runAction("export")} disabled={isBusy}>Export zip</button>
        </div>
      </div>
      <div className="form-grid">
        <TextInput label="Package id" value={packageId} onChange={setPackageId} />
        <TextInput label="Name" value={name} onChange={setName} />
        <TextInput label="Quests" value={quests} onChange={setQuests} />
        <TextInput label="Characters" value={characters} onChange={setCharacters} />
        <TextInput label="Templates" value={templates} onChange={setTemplates} />
        <TextInput label="Scenarios" value={scenarios} onChange={setScenarios} />
        <TextInput label="Dependencies" value={dependencies} onChange={setDependencies} />
        <TextInput label="Conflicts" value={conflicts} onChange={setConflicts} />
        <TextInput label="Package file path" value={filePath} onChange={setFilePath} />
      </div>
      <label className="field wide-field">
        <span>Package file content</span>
        <textarea value={fileContent} onChange={(event) => setFileContent(event.target.value)} rows={5} disabled={isBusy} />
      </label>
      {report && (
        <div className="preview-panel">
          <dl className="summary-list compact">
            <dt>Validation</dt>
            <dd>{report.validation.ok ? "OK" : "Blocked"}</dd>
            <dt>Files</dt>
            <dd>{report.files.length}</dd>
            <dt>Checksums</dt>
            <dd>{Object.keys(report.manifest.checksums).length}</dd>
            <dt>Applied</dt>
            <dd>{report.applied ? "Yes" : "No"}</dd>
          </dl>
          <ValidationPanel validation={report.validation} onSelectIssue={() => undefined} />
          <h4>Dependencies / conflicts</h4>
          <p className="muted">Dependencies: {report.dependencies.join(", ") || "none"}</p>
          <p className="muted">Conflicts: {report.conflicts.join(", ") || "none"}</p>
          <h4>Normal manifest</h4>
          <AuthoringPreviewCode content={JSON.stringify(report.normal_manifest, null, 2)} />
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} compact />
    </section>
  );
}

function CampaignStarterKitBuilderPanel() {
  const [draft, setDraft] = useState<CampaignStarterKitDraft>(() => defaultCampaignStarterKitDraft());
  const [preview, setPreview] = useState<CampaignStarterKitPreview | null>(null);
  const [exportReport, setExportReport] = useState<ScriptPackageBuildReport | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  function updateDraft(patch: Partial<CampaignStarterKitDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
  }

  async function runPreview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewCampaignStarterKit(draft);
      setPreview(response);
      setMessage("Campaign starter preview ready.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function runBuild() {
    if (!confirmDangerousAction("Build this campaign starter draft after validation and quality dry-run?")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await buildCampaignStarterKit(draft, true);
      setPreview(response);
      setMessage(response.built ? "Campaign starter build passed dry-run gates." : "Campaign starter build blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function runExportScript() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await exportCampaignStarterScriptPackage(draft);
      setExportReport(response);
      setMessage(response.archive_file_name ? `Script package export ready: ${response.archive_file_name}` : "Script package export blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="authoring-card">
      <div className="section-heading">
        <div>
          <h3>Campaign Starter Kit Builder</h3>
          <p>Assemble a playable local starter from world, NPC, quest, faction, mystery, scenario, quality, and script drafts.</p>
        </div>
        <div className="button-row">
          <button onClick={() => void runPreview()} disabled={isBusy}>Preview</button>
          <button onClick={() => void runBuild()} disabled={isBusy}>Build dry-run</button>
          <button onClick={() => void runExportScript()} disabled={isBusy}>Export script package</button>
        </div>
      </div>
      <div className="form-grid">
        <TextInput label="Campaign id" value={draft.campaign_id} onChange={(value) => updateDraft({ campaign_id: value })} />
        <TextInput label="Name" value={draft.name} onChange={(value) => updateDraft({ name: value })} />
        <TextInput label="Genre" value={draft.genre} onChange={(value) => updateDraft({ genre: value })} />
        <TextInput label="Tone" value={draft.tone} onChange={(value) => updateDraft({ tone: value })} />
        <TextInput label="Starting region" value={draft.starting_region} onChange={(value) => updateDraft({ starting_region: value })} />
        <TextInput label="Core conflict" value={draft.core_conflict} onChange={(value) => updateDraft({ core_conflict: value })} />
        <label className="field">
          <span>NPC count</span>
          <input type="number" min={1} max={20} value={draft.npc_count} onChange={(event) => updateDraft({ npc_count: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <label className="field">
          <span>Questlines</span>
          <input type="number" min={1} max={10} value={draft.questline_count} onChange={(event) => updateDraft({ questline_count: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <label className="field">
          <span>Factions</span>
          <input type="number" min={0} max={10} value={draft.faction_count} onChange={(event) => updateDraft({ faction_count: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <TextInput label="RP focus" value={draft.RP_focus_level} onChange={(value) => updateDraft({ RP_focus_level: value })} />
        <label className="field">
          <span>Playtime hours</span>
          <input type="number" min={1} max={40} value={draft.target_playtime_hours} onChange={(event) => updateDraft({ target_playtime_hours: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <label className="field checkbox-field">
          <input type="checkbox" checked={draft.mystery_enabled} onChange={(event) => updateDraft({ mystery_enabled: event.target.checked })} disabled={isBusy} />
          <span>Mystery enabled</span>
        </label>
      </div>
      {preview && (
        <div className="preview-panel">
          <dl className="summary-list compact">
            <dt>Validation</dt>
            <dd>{preview.validation.ok ? "OK" : "Blocked"}</dd>
            <dt>Quality dry-run</dt>
            <dd>{preview.quality_gate_dry_run.passed ? "passed" : "blocked"}</dd>
            <dt>Scenarios</dt>
            <dd>{preview.scenario_regression_suite.length}</dd>
            <dt>Built</dt>
            <dd>{preview.built ? "Yes" : "No"}</dd>
          </dl>
          <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />
          <h4>Generated content</h4>
          <ul className="compact-list">
            <li>World: {preview.world_pack_draft.world_id}</li>
            <li>NPC pack: {preview.npc_pack_draft.pack_id}</li>
            <li>Quest pack: {preview.quest_pack_draft.pack_id}</li>
            <li>Script package: {preview.script_package_draft.manifest.package_id}</li>
          </ul>
          <h4>Quality gate dry-run</h4>
          <AuthoringPreviewCode content={JSON.stringify(preview.quality_gate_dry_run, null, 2)} />
        </div>
      )}
      {exportReport && (
        <div className="preview-panel">
          <h4>Script package export</h4>
          <p className="muted">{exportReport.archive_file_name || "No archive generated"}</p>
          <ValidationPanel validation={exportReport.validation} onSelectIssue={() => undefined} />
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} compact />
    </section>
  );
}

function defaultCampaignStarterKitDraft(): CampaignStarterKitDraft {
  return {
    campaign_id: "starter_mist",
    name: "Starter Mist",
    genre: "mystery",
    tone: "grounded",
    starting_region: "square",
    core_conflict: "missing heirloom",
    npc_count: 3,
    questline_count: 1,
    faction_count: 2,
    mystery_enabled: true,
    RP_focus_level: "medium",
    target_playtime_hours: 2,
    llm_assisted: false
  };
}

function defaultTemplateWizardDraft(worldId: string): TemplateWizardDraft {
  return {
    id: "wizard_template",
    name: "Wizard Template",
    template_type: "questline",
    current_step: "choose_template_type",
    variables: {},
    target_world_id: worldId,
    save_as_template: false
  };
}

const WORLD_PACK_WIZARD_SYSTEMS = ["quests", "roleplay", "npc_simulation", "factions", "rumors"] as const;

function WorldPackWizardPanel() {
  const [draft, setDraft] = useState<WorldPackWizardDraft>(() => defaultWorldPackWizardDraft());
  const [preview, setPreview] = useState<WorldPackWizardPreviewResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  function updateDraft(patch: Partial<WorldPackWizardDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
    setPreview(null);
  }

  function toggleSystem(system: string) {
    const systems = draft.enabled_systems.includes(system)
      ? draft.enabled_systems.filter((item) => item !== system)
      : [...draft.enabled_systems, system];
    updateDraft({ enabled_systems: systems });
  }

  async function handlePreview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewWorldPackWizard(draft);
      setPreview(response);
      setMessage(response.validation?.ok ? "World pack preview generated without writing files." : "Preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateWorldPackWizard(draft);
      setPreview(response);
      setMessage(response.validation?.ok ? "World pack draft validates." : "World pack draft needs changes.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApply() {
    if (!confirmDangerousAction("Create this new local world pack after validation? Existing worlds are not overwritten.")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyWorldPackWizard(draft, true, true);
      setPreview(response);
      setMessage(response.applied ? "World pack created after validation gate approval." : "World pack apply was blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>World Pack Wizard</h2>
          <p className="muted">Basic info, genre, starting region, systems, preview, validation, and explicit apply.</p>
        </div>
        <span className="badge">{preview?.draft.current_step ?? draft.current_step ?? "basic_info"}</span>
      </div>
      <div className="template-grid">
        <TextInput label="World id" value={draft.world_id} onChange={(value) => updateDraft({ world_id: value })} />
        <TextInput label="Name" value={draft.name} onChange={(value) => updateDraft({ name: value })} />
        <TextInput label="Genre" value={draft.genre} onChange={(value) => updateDraft({ genre: value })} />
        <TextInput label="Tone" value={draft.tone} onChange={(value) => updateDraft({ tone: value })} />
        <TextInput label="Starting location" value={draft.starting_location} onChange={(value) => updateDraft({ starting_location: value })} />
        <label>
          Locations
          <input
            type="number"
            min={1}
            max={20}
            value={draft.location_seed_count}
            onChange={(event) => updateDraft({ location_seed_count: Number(event.target.value) })}
            disabled={isBusy}
          />
        </label>
        <label>
          NPCs
          <input
            type="number"
            min={0}
            max={50}
            value={draft.npc_seed_count}
            onChange={(event) => updateDraft({ npc_seed_count: Number(event.target.value) })}
            disabled={isBusy}
          />
        </label>
        <label>
          Quests
          <input
            type="number"
            min={0}
            max={50}
            value={draft.quest_seed_count}
            onChange={(event) => updateDraft({ quest_seed_count: Number(event.target.value) })}
            disabled={isBusy}
          />
        </label>
        <TextInput label="Prompt profile" value={draft.default_prompt_profile} onChange={(value) => updateDraft({ default_prompt_profile: value })} />
        <TextInput label="Quality profile" value={draft.default_quality_profile} onChange={(value) => updateDraft({ default_quality_profile: value })} />
      </div>
      <label className="full-width-field">
        Description
        <textarea value={draft.description} onChange={(event) => updateDraft({ description: event.target.value })} disabled={isBusy} />
      </label>
      <div className="reference-picker-results">
        {WORLD_PACK_WIZARD_SYSTEMS.map((system) => (
          <label key={system}>
            <input
              type="checkbox"
              checked={draft.enabled_systems.includes(system)}
              onChange={() => toggleSystem(system)}
              disabled={isBusy}
            />
            {system}
          </label>
        ))}
      </div>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>Preview</button>
        <button type="button" onClick={() => void handleValidate()} disabled={isBusy}>Validate</button>
        <button type="button" onClick={() => void handleApply()} disabled={isBusy}>Apply</button>
      </div>
      {preview?.validation && <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />}
      {preview && (
        <div className="template-preview">
          <h3>Generated World Pack Files</h3>
          {preview.generated_files.map((file) => (
            <details key={file.file_name} open>
              <summary>{file.file_name}</summary>
              <AuthoringPreviewCode content={file.content} />
            </details>
          ))}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function defaultWorldPackWizardDraft(): WorldPackWizardDraft {
  return {
    world_id: "new_world",
    name: "New World",
    genre: "mystery",
    tone: "grounded",
    description: "A local world pack draft.",
    starting_location: "start",
    location_seed_count: 1,
    npc_seed_count: 1,
    quest_seed_count: 1,
    enabled_systems: ["quests", "roleplay", "npc_simulation"],
    default_prompt_profile: "default_safe",
    default_quality_profile: "standard",
    llm_assisted: false,
    current_step: "basic_info"
  };
}

function NPCPackGeneratorPanel({ worldId, onOpenEditor }: { worldId: string; onOpenEditor: (toolId: AuthoringToolId) => void }) {
  const [draft, setDraft] = useState<NPCPackGeneratorDraft>(() => defaultNPCPackGeneratorDraft(worldId));
  const [factionText, setFactionText] = useState<string>("village_council");
  const [locationText, setLocationText] = useState<string>("village_square, blacksmith");
  const [archetypeText, setArchetypeText] = useState<string>("guard, informant, merchant");
  const [presetText, setPresetText] = useState<string>("guard");
  const [preview, setPreview] = useState<NPCPackGeneratorPreviewResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    setDraft((current) => ({ ...current, target_world_id: worldId }));
  }, [worldId]);

  function buildDraft(): NPCPackGeneratorDraft {
    return {
      ...draft,
      target_world_id: worldId,
      faction_ids: parseCommaList(factionText),
      location_ids: parseCommaList(locationText),
      archetypes: parseCommaList(archetypeText),
      simulation_preset_ids: parseCommaList(presetText)
    };
  }

  function updateDraft(patch: Partial<NPCPackGeneratorDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
    setPreview(null);
  }

  async function handlePreview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewNPCPackGenerator(buildDraft());
      setPreview(response);
      setMessage(response.validation.ok ? "NPC pack preview generated without writing files." : "NPC pack preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateNPCPackGenerator(buildDraft());
      setPreview(response);
      setMessage(response.validation.ok ? "NPC pack draft validates." : "NPC pack draft needs changes.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApply() {
    if (!confirmDangerousAction("Apply generated NPC draft to the local world pack after validation? Active GameState is not changed.")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyNPCPackGenerator(buildDraft(), true, true);
      setPreview(response);
      setMessage(response.applied ? "NPC pack applied to content files after validation." : "NPC pack apply was blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleExport() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await exportNPCPackGenerator(buildDraft(), true);
      setPreview(response);
      setMessage(response.exported_pack ? "Safe character pack export preview is ready." : "Export was blocked by validation.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>NPC Pack Generator</h2>
          <p className="muted">Generate editable NPC candidates with RP profiles, voice, goals, schedules, and hidden-safe secrets.</p>
        </div>
        <button type="button" onClick={() => onOpenEditor("rp_characters")}>Open RP Editor</button>
      </div>
      <div className="template-grid">
        <TextInput label="Pack id" value={draft.pack_id} onChange={(value) => updateDraft({ pack_id: value })} />
        <TextInput label="Theme" value={draft.theme} onChange={(value) => updateDraft({ theme: value })} />
        <TextInput label="RP style" value={draft.rp_style} onChange={(value) => updateDraft({ rp_style: value })} />
        <label>
          NPC count
          <input type="number" min={1} max={50} value={draft.npc_count} onChange={(event) => updateDraft({ npc_count: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <label>
          Relationship density
          <input type="number" min={0} max={1} step={0.05} value={draft.relationship_density} onChange={(event) => updateDraft({ relationship_density: Number(event.target.value) })} disabled={isBusy} />
        </label>
        <label>
          Hidden secret ratio
          <input type="number" min={0} max={1} step={0.05} value={draft.hidden_secret_ratio} onChange={(event) => updateDraft({ hidden_secret_ratio: Number(event.target.value) })} disabled={isBusy} />
        </label>
      </div>
      <div className="template-grid">
        <TextInput label="Faction ids" value={factionText} onChange={setFactionText} />
        <TextInput label="Location ids" value={locationText} onChange={setLocationText} />
        <TextInput label="Archetypes" value={archetypeText} onChange={setArchetypeText} />
        <TextInput label="Simulation presets" value={presetText} onChange={setPresetText} />
      </div>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>Preview</button>
        <button type="button" onClick={() => void handleValidate()} disabled={isBusy}>Validate</button>
        <button type="button" onClick={() => void handleApply()} disabled={isBusy}>Apply</button>
        <button type="button" onClick={() => void handleExport()} disabled={isBusy}>Safe Export</button>
      </div>
      {preview?.validation && <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />}
      {preview && (
        <div className="template-preview">
          <h3>NPC Candidates</h3>
          <div className="card-grid">
            {preview.generated.npc_candidates.map((npc) => (
              <article className="summary-card" key={npc.id}>
                <h4>{npc.name}</h4>
                <p className="muted">{npc.id} · {npc.archetype} · {npc.location_id}</p>
                <p>{npc.personality}</p>
                {npc.hidden_secrets.length > 0 && <span className="badge">hidden secrets: {npc.hidden_secrets.length}</span>}
              </article>
            ))}
          </div>
          <h3>Generated YAML</h3>
          {Object.entries(preview.yaml_contents).map(([fileName, content]) => (
            <details key={fileName}>
              <summary>{fileName}</summary>
              <AuthoringPreviewCode content={content} />
            </details>
          ))}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function defaultNPCPackGeneratorDraft(worldId: string): NPCPackGeneratorDraft {
  return {
    target_world_id: worldId,
    pack_id: "npc_pack",
    theme: "local ensemble",
    faction_ids: [],
    location_ids: [],
    npc_count: 3,
    archetypes: ["guard", "informant", "merchant"],
    rp_style: "grounded",
    simulation_preset_ids: [],
    relationship_density: 0.25,
    hidden_secret_ratio: 0,
    llm_assisted: false
  };
}

function QuestPackGeneratorPanel({ worldId }: { worldId: string }) {
  const [draft, setDraft] = useState<QuestPackGeneratorDraft>(() => defaultQuestPackGeneratorDraft(worldId));
  const [npcText, setNpcText] = useState<string>("harlan");
  const [locationText, setLocationText] = useState<string>("village_square, old_bridge");
  const [factionText, setFactionText] = useState<string>("village_council");
  const [factText, setFactText] = useState<string>("");
  const [preview, setPreview] = useState<QuestPackGeneratorPreviewResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    setDraft((current) => ({ ...current, target_world_id: worldId }));
  }, [worldId]);

  function updateDraft(patch: Partial<QuestPackGeneratorDraft>) {
    setDraft((current) => ({ ...current, ...patch }));
    setPreview(null);
  }

  function buildDraft(): QuestPackGeneratorDraft {
    return {
      ...draft,
      target_world_id: worldId,
      involved_npcs: parseCommaList(npcText),
      involved_locations: parseCommaList(locationText),
      involved_factions: parseCommaList(factionText),
      required_facts: parseCommaList(factText)
    };
  }

  async function handlePreview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewQuestPackGenerator(buildDraft());
      setPreview(response);
      setMessage(response.validation.ok ? "Quest pack preview generated without writing files." : "Quest pack preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateQuestPackGenerator(buildDraft());
      setPreview(response);
      setMessage(response.validation.ok ? "Quest pack draft validates." : "Quest pack draft needs changes.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApply() {
    if (!confirmDangerousAction("Apply generated quest draft to local content files after validation? Active saves are not changed.")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyQuestPackGenerator(buildDraft(), true, true);
      setPreview(response);
      setMessage(response.applied ? "Quest pack applied after validation." : "Quest pack apply was blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Quest Pack Generator</h2>
          <p className="muted">Generate structurally safe questline drafts, scenario regression candidates, and quest graph previews.</p>
        </div>
        <span className="badge">{preview?.generated.scenario_regression_candidates.length ?? 0} scenarios</span>
      </div>
      <div className="template-grid">
        <TextInput label="Pack id" value={draft.pack_id} onChange={(value) => updateDraft({ pack_id: value })} />
        <TextInput label="Theme" value={draft.theme} onChange={(value) => updateDraft({ theme: value })} />
        <TextInput label="Reward policy" value={draft.reward_policy} onChange={(value) => updateDraft({ reward_policy: value })} />
        <label>
          Quest count
          <input type="number" min={1} max={20} value={draft.quest_count} onChange={(event) => updateDraft({ quest_count: Number(event.target.value) })} disabled={isBusy} />
        </label>
      </div>
      <div className="template-grid">
        <TextInput label="NPC ids" value={npcText} onChange={setNpcText} />
        <TextInput label="Location ids" value={locationText} onChange={setLocationText} />
        <TextInput label="Faction ids" value={factionText} onChange={setFactionText} />
        <TextInput label="Required facts" value={factText} onChange={setFactText} />
      </div>
      <div className="reference-picker-results">
        <label>
          <input type="checkbox" checked={draft.mystery_mode} onChange={(event) => updateDraft({ mystery_mode: event.target.checked })} disabled={isBusy} />
          Mystery mode
        </label>
        <label>
          <input type="checkbox" checked={draft.failure_paths_enabled} onChange={(event) => updateDraft({ failure_paths_enabled: event.target.checked })} disabled={isBusy} />
          Failure paths
        </label>
      </div>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy}>Preview</button>
        <button type="button" onClick={() => void handleValidate()} disabled={isBusy}>Validate</button>
        <button type="button" onClick={() => void handleApply()} disabled={isBusy}>Apply</button>
      </div>
      {preview?.validation && <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />}
      {preview?.generated.quality_checks && preview.generated.quality_checks.warnings.length > 0 && (
        <ValidationPanel validation={preview.generated.quality_checks} onSelectIssue={() => undefined} />
      )}
      {preview && (
        <div className="template-preview">
          <h3>Quest Candidates</h3>
          <div className="card-grid">
            {preview.generated.quest_candidates.map((quest) => (
              <article className="summary-card" key={String(quest.id)}>
                <h4>{String(quest.title ?? quest.id)}</h4>
                <p className="muted">{String(quest.id)} · {String(quest.initial_stage)}</p>
                <p>{String(quest.description ?? "")}</p>
              </article>
            ))}
          </div>
          <h3>Scenario Regression Drafts</h3>
          {preview.generated.scenario_regression_candidates.map((scenario) => (
            <p className="muted" key={String(scenario.id)}>{String(scenario.id)} · {String(scenario.name)}</p>
          ))}
          <h3>Generated YAML</h3>
          {Object.entries(preview.yaml_contents).map(([fileName, content]) => (
            <details key={fileName}>
              <summary>{fileName}</summary>
              <AuthoringPreviewCode content={content} />
            </details>
          ))}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function defaultQuestPackGeneratorDraft(worldId: string): QuestPackGeneratorDraft {
  return {
    target_world_id: worldId,
    pack_id: "quest_pack",
    theme: "local mystery",
    quest_count: 1,
    involved_npcs: [],
    involved_locations: [],
    involved_factions: [],
    required_facts: [],
    mystery_mode: false,
    failure_paths_enabled: false,
    reward_policy: "story",
    llm_assisted: false
  };
}

function LocationClusterTemplatePanel({ worldId }: { worldId: string }) {
  const [templates, setTemplates] = useState<LocationClusterTemplate[]>([]);
  const [templateId, setTemplateId] = useState<string>("");
  const [variablesText, setVariablesText] = useState<string>("prefix=river\ndisplay_name=River Gate");
  const [preview, setPreview] = useState<LocationClusterPreviewResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadTemplates();
  }, []);

  async function loadTemplates() {
    setError("");
    try {
      const response = await fetchLocationClusterTemplates();
      setTemplates(response.templates);
      setTemplateId((current) => current || response.templates[0]?.id || "");
    } catch (err) {
      setError(authoringErrorMessage(err));
    }
  }

  async function handlePreview() {
    if (!templateId) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewLocationClusterTemplate(templateId, worldId, parseKeyValueLines(variablesText));
      setPreview(response);
      setMessage(response.validation.ok ? "Location cluster preview generated without writing files." : "Location cluster preview has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApply() {
    if (!templateId || !confirmDangerousAction("Apply this location cluster draft to locations.yaml after validation? Active GameState is not changed.")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyLocationClusterTemplate(templateId, worldId, parseKeyValueLines(variablesText), true, true);
      setPreview(response);
      setMessage(response.applied ? "Location cluster applied after validation." : "Location cluster apply was blocked.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selected = templates.find((template) => template.id === templateId);
  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Location Cluster Templates</h2>
          <p className="muted">Create connected location groups with authoring-only hidden paths and map validation.</p>
        </div>
        <span className="badge">{selected?.cluster_type ?? "cluster"}</span>
      </div>
      <div className="template-grid">
        <label>
          Template
          <select value={templateId} onChange={(event) => { setTemplateId(event.target.value); setPreview(null); }} disabled={isBusy}>
            {templates.map((template) => <option key={template.id} value={template.id}>{template.name}</option>)}
          </select>
        </label>
        <label className="full-width-field">
          Variables
          <textarea value={variablesText} onChange={(event) => setVariablesText(event.target.value)} disabled={isBusy} />
        </label>
      </div>
      {selected && (
        <p className="muted">
          Required: {selected.required_variables.join(", ") || "none"} · Nodes: {selected.location_nodes.length} · Hidden edges: {selected.optional_hidden_edges.length}
        </p>
      )}
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy || !templateId}>Preview</button>
        <button type="button" onClick={() => void handleApply()} disabled={isBusy || !templateId}>Apply Draft</button>
      </div>
      {preview?.validation && <ValidationPanel validation={preview.validation} onSelectIssue={() => undefined} />}
      {preview && (
        <div className="template-preview">
          <h3>Map Preview</h3>
          <MapEditorSvg
            graph={preview.graph}
            selectedNodeId=""
            selectedEdgeIndex={-1}
            onSelectNode={() => undefined}
            onSelectEdge={() => undefined}
            draggingNodeId=""
            onDragStart={() => undefined}
            onDragEnd={() => undefined}
            onMoveNode={() => undefined}
          />
          <h3>Generated locations.yaml</h3>
          <AuthoringPreviewCode content={preview.yaml_content} />
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function parseCommaList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function parseKeyValueLines(value: string): Record<string, string> {
  const result: Record<string, string> = {};
  value.split("\n").forEach((line) => {
    const index = line.indexOf("=");
    if (index > 0) {
      result[line.slice(0, index).trim()] = line.slice(index + 1).trim();
    }
  });
  return result;
}

function WorldMergeAssistantPanel({ worldId }: { worldId: string }) {
  const [branches, setBranches] = useState<WorldBranch[]>([]);
  const [ours, setOurs] = useState<string>("");
  const [theirs, setTheirs] = useState<string>("");
  const [resolutions, setResolutions] = useState<MergeResolution[]>([]);
  const [customText, setCustomText] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState<WorldMergeDraft | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadBranches();
  }, [worldId]);

  async function loadBranches() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchWorldBranches(worldId);
      setBranches(response.branches);
      setOurs((current) => current || response.branches[0]?.branch_id || "");
      setTheirs((current) => current || response.branches[1]?.branch_id || response.branches[0]?.branch_id || "");
    } catch (err) {
      setBranches([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePreview() {
    if (!ours || !theirs) {
      setError("Choose two branches before previewing a merge.");
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewWorldMerge(worldId, ours, theirs, materializeCustomResolutions(resolutions, customText));
      setDraft(response);
      setMessage(response.validation.ok ? "Merge draft validates." : "Merge draft has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!ours || !theirs) {
      return;
    }
    if (!confirmDangerousAction("Save this merge result to the local world pack after validation?")) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await saveWorldMerge(worldId, ours, theirs, materializeCustomResolutions(resolutions, customText), true);
      setDraft(response);
      setMessage(response.saved ? "Merge result saved after validation." : "Merge save was blocked by validation or unresolved warnings.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateResolution(conflictId: string, choice: MergeResolution["choice"]) {
    setResolutions((current) => {
      const next = current.filter((resolution) => resolution.conflict_id !== conflictId);
      return [...next, { conflict_id: conflictId, choice }];
    });
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>World Branch Merge Assistant</h2>
          <p className="muted">Preview merge drafts, choose conflict resolutions, and save only after backend validation.</p>
        </div>
        <button type="button" onClick={() => void loadBranches()} disabled={isBusy}>Refresh Branches</button>
      </div>
      <div className="template-grid">
        <label>Ours<select value={ours} onChange={(event) => setOurs(event.target.value)} disabled={isBusy}>{branches.map((branch) => <option key={branch.branch_id} value={branch.branch_id}>{branch.name || branch.branch_id}</option>)}</select></label>
        <label>Theirs<select value={theirs} onChange={(event) => setTheirs(event.target.value)} disabled={isBusy}>{branches.map((branch) => <option key={branch.branch_id} value={branch.branch_id}>{branch.name || branch.branch_id}</option>)}</select></label>
      </div>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreview()} disabled={isBusy || !ours || !theirs}>Merge Preview</button>
        <button type="button" onClick={() => void handleSave()} disabled={isBusy || !draft}>Explicit Save</button>
      </div>
      {draft?.validation && <ValidationPanel validation={draft.validation} onSelectIssue={() => undefined} />}
      {draft && (
        <div className="template-preview">
          <h3>Conflicts</h3>
          {draft.conflicts.length ? draft.conflicts.map((conflict) => (
            <div key={conflict.conflict_id} className="diff-summary">
              <strong>{conflict.conflict_type}</strong>
              <p>{conflict.file_name} / {conflict.entity_id}: {conflict.message}</p>
              <select value={resolutions.find((item) => item.conflict_id === conflict.conflict_id)?.choice ?? "base"} onChange={(event) => updateResolution(conflict.conflict_id, event.target.value as MergeResolution["choice"])}>
                <option value="base">base</option>
                <option value="ours">ours</option>
                <option value="theirs">theirs</option>
                <option value="custom">custom</option>
              </select>
              {(resolutions.find((item) => item.conflict_id === conflict.conflict_id)?.choice === "custom") && (
                <textarea value={customText[conflict.conflict_id] ?? JSON.stringify(conflict.base ?? {}, null, 2)} onChange={(event) => setCustomText({ ...customText, [conflict.conflict_id]: event.target.value })} />
              )}
            </div>
          )) : <EmptyState title="No conflicts." detail="The merge draft can be validated and saved explicitly." />}
          <h3>Merge Draft Files</h3>
          {Object.entries(draft.proposed_files).slice(0, 3).map(([fileName, content]) => <details key={fileName}><summary>{fileName}</summary><AuthoringPreviewCode content={content} /></details>)}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function materializeCustomResolutions(resolutions: MergeResolution[], customText: Record<string, string>): MergeResolution[] {
  return resolutions.map((resolution) => {
    if (resolution.choice !== "custom") {
      return resolution;
    }
    try {
      return { ...resolution, custom: JSON.parse(customText[resolution.conflict_id] ?? "{}") as Record<string, unknown> };
    } catch {
      return resolution;
    }
  });
}

function ContentDiffReviewPanel({ worldId, fileName, content, onJump }: { worldId: string; fileName: string; content: string; onJump: (toolId: AuthoringToolId) => void }) {
  const [viewMode, setViewMode] = useState<"file" | "entity" | "graph">("entity");
  const [review, setReview] = useState<ContentDiffReview | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  async function handleReview() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await reviewContentDiff(
        { world_id: worldId },
        { world_id: worldId, files: { [fileName]: content } },
        ["file_diff", "entity_diff", "graph_diff", "package_diff", "schema_diff", "visibility_diff", "rp_profile_diff"],
        true
      );
      setReview(response);
      setMessage("Diff review generated. Hidden details are redacted in normal view.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const visibleChanges = review
    ? viewMode === "file"
      ? [...review.added, ...review.removed, ...review.changed]
      : viewMode === "graph"
        ? review.changed.filter((item) => item.diff_type === "graph_diff")
        : [...review.added, ...review.removed, ...review.changed].filter((item) => item.diff_type !== "graph_diff")
    : [];

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Content Diff Review</h2>
          <p className="muted">Review current YAML draft against disk content without saving or exposing hidden details.</p>
        </div>
        <button type="button" onClick={() => void handleReview()} disabled={isBusy}>Review Current Draft</button>
      </div>
      <div className="authoring-header-actions">
        <button type="button" className={viewMode === "file" ? "active" : ""} onClick={() => setViewMode("file")}>File View</button>
        <button type="button" className={viewMode === "entity" ? "active" : ""} onClick={() => setViewMode("entity")}>Entity View</button>
        <button type="button" className={viewMode === "graph" ? "active" : ""} onClick={() => setViewMode("graph")}>Graph View</button>
      </div>
      {review && (
        <>
          <div className="diff-summary">
            <h3>Changes</h3>
            {visibleChanges.length ? visibleChanges.map((item) => (
              <p key={`${item.file_name}:${item.entity_id}:${item.diff_type}`}>
                <strong>{item.diff_type}</strong> {item.file_name}/{item.entity_id}: {item.summary}
                <button type="button" onClick={() => onJump(toolForFile(item.file_name))}>Open editor</button>
              </p>
            )) : <p className="muted">No changes for this view.</p>}
          </div>
          <div className="diff-summary">
            <h3>Visibility / Migration</h3>
            {review.visibility_risk.map((risk) => <p key={risk} className="danger-text">{risk}</p>)}
            {review.migration_impact.map((impact) => <p key={impact}>{impact}</p>)}
            {review.renamed_candidates.map((candidate) => <p key={candidate}>Rename candidate: {candidate}</p>)}
          </div>
          <div className="diff-summary">
            <h3>Validation Issues</h3>
            {review.validation_issues.length ? review.validation_issues.map((issue) => <p key={issue}>{issue}</p>) : <p className="muted">No validation issues.</p>}
          </div>
        </>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

const LIBRARY_TYPES: Array<"all" | LocalContentType> = [
  "all",
  "world",
  "character_pack",
  "quest_pack",
  "NPC_pack",
  "template_pack",
  "scenario_suite",
  "prompt_profile",
  "RP_profile",
  "mod",
  "script_package",
  "campaign_starter"
];

function LocalContentLibraryPanel({ onOpenEditor }: { onOpenEditor: (toolId: AuthoringToolId) => void }) {
  const [items, setItems] = useState<LocalContentLibraryItem[]>([]);
  const [filter, setFilter] = useState<"all" | LocalContentType>("all");
  const [query, setQuery] = useState<string>("");
  const [tagFilter, setTagFilter] = useState<string>("");
  const [selectedId, setSelectedId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [batchReport, setBatchReport] = useState<Record<string, unknown> | null>(null);
  const [archiveDraft, setArchiveDraft] = useState<string>("");
  const [exportProfiles, setExportProfiles] = useState<ExportProfile[]>([]);
  const [importProfiles, setImportProfiles] = useState<ImportProfile[]>([]);
  const [selectedExportProfileId, setSelectedExportProfileId] = useState<string>("safe");
  const [selectedImportProfileId, setSelectedImportProfileId] = useState<string>("safe");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadItems();
  }, [filter, query, tagFilter]);

  useEffect(() => {
    void loadProfiles();
  }, []);

  async function loadProfiles() {
    try {
      const catalog = await fetchImportExportProfiles();
      setExportProfiles(catalog.export_profiles);
      setImportProfiles(catalog.import_profiles);
    } catch {
      setExportProfiles([]);
      setImportProfiles([]);
    }
  }

  async function loadItems() {
    setIsBusy(true);
    setError("");
    try {
      const tags = tagFilter.trim() ? commaList(tagFilter) : [];
      const response = query.trim() || tags.length
        ? await searchLocalContentLibrary(query, filter === "all" ? [] : [filter], tags)
        : await fetchLocalContentLibrary(filter);
      setItems(response.items);
      setSelectedId((current) => response.items.some((item) => item.id === current) ? current : response.items[0]?.id ?? "");
    } catch (err) {
      setItems([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selected = items.find((item) => item.id === selectedId) ?? items[0] ?? null;

  async function handleValidate() {
    if (!selected) return;
    setIsBusy(true);
    setError("");
    try {
      const response = await validateLocalContentLibraryItem(selected.id);
      setValidation(response);
      setMessage(response.ok ? "Library item validates." : "Library item has validation issues.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleExport() {
    if (!selected) return;
    setIsBusy(true);
    setError("");
    try {
      const response = await exportLocalContentLibraryItem(selected.content_type, selected.id, selectedExportProfileId);
      setArchiveDraft(response.archive_base64);
      setMessage(`Export ready: ${response.file_name}`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleImport(confirmApply: boolean) {
    if (!archiveDraft.trim()) {
      setError("Paste a local archive payload first.");
      return;
    }
    if (confirmApply && !confirmDangerousAction(DANGEROUS_ACTION_COPY.importPackageApply)) {
      return;
    }
    setIsBusy(true);
    setError("");
    try {
      const response = await importLocalContentLibraryArchive(archiveDraft.trim(), false, confirmApply, selectedImportProfileId);
      setMessage(JSON.stringify(response));
      void loadItems();
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleBatchValidate() {
    setIsBusy(true);
    setError("");
    try {
      const response = await batchValidateLocalContentLibrary(items.map((item) => item.id), filter === "all" ? [] : [filter]);
      setBatchReport(response);
      setMessage("Batch validation complete.");
    } catch (err) {
      setBatchReport(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Local Content Library</h2>
          <p className="muted">Worlds, character packs, templates, scenario suites, prompt/RP profiles, and mods.</p>
        </div>
        <button type="button" onClick={() => void loadItems()} disabled={isBusy}>Refresh Library</button>
      </div>
      <div className="template-grid">
        <label>Type<select value={filter} onChange={(event) => setFilter(event.target.value as "all" | LocalContentType)}>{LIBRARY_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}</select></label>
        <TextInput label="Search" value={query} onChange={setQuery} />
        <TextInput label="Tags" value={tagFilter} onChange={setTagFilter} />
        <label>Item<select value={selected?.id ?? ""} onChange={(event) => setSelectedId(event.target.value)}>{items.map((item) => <option key={`${item.content_type}:${item.id}`} value={item.id}>{item.name}</option>)}</select></label>
        <label>
          Export profile
          <select value={selectedExportProfileId} onChange={(event) => setSelectedExportProfileId(event.target.value)}>
            {exportProfiles.length === 0 && <option value="safe">Safe Export</option>}
            {exportProfiles.map((profile) => <option key={profile.profile_id} value={profile.profile_id}>{profile.name}</option>)}
          </select>
        </label>
        <label>
          Import profile
          <select value={selectedImportProfileId} onChange={(event) => setSelectedImportProfileId(event.target.value)}>
            {importProfiles.length === 0 && <option value="safe">Safe Import</option>}
            {importProfiles.map((profile) => <option key={profile.profile_id} value={profile.profile_id}>{profile.name}</option>)}
          </select>
        </label>
      </div>
      {selected ? (
        <div className="diff-summary">
          <h3>{selected.name}</h3>
          <p>{selected.content_type} / {selected.id}</p>
          <p className="muted">{selected.description || "No description."}</p>
          <p>Path: {selected.path_label}</p>
          <p>Tags: {selected.tags.length ? selected.tags.join(", ") : "none"}</p>
          <p>Dependencies: {selected.dependencies.length ? selected.dependencies.join(", ") : "none"}</p>
          <AuthoringPreviewCode content={JSON.stringify(selected.quality_summary, null, 2)} />
          <AuthoringPreviewCode content={JSON.stringify(selected.metadata, null, 2)} />
          <div className="authoring-header-actions">
            <button type="button" onClick={() => void handleValidate()} disabled={isBusy || !selected.capabilities.includes("validate")}>Validate</button>
            <button type="button" onClick={() => void handleExport()} disabled={isBusy || !selected.capabilities.includes("export")}>Export</button>
            <button type="button" onClick={() => void handleBatchValidate()} disabled={isBusy || items.length === 0}>Batch Validate</button>
            <button type="button" onClick={() => onOpenEditor(libraryToolForItem(selected))}>Open Editor</button>
          </div>
        </div>
      ) : <EmptyState title="No content items." detail="The local library did not find matching items." />}
      {validation && <ValidationPanel validation={validation} onSelectIssue={() => undefined} />}
      {batchReport && <AuthoringPreviewCode content={JSON.stringify(batchReport, null, 2)} />}
      <label className="full-width-field">Import archive payload<textarea value={archiveDraft} onChange={(event) => setArchiveDraft(event.target.value)} /></label>
      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handleImport(false)} disabled={isBusy}>Import Dry-run</button>
        <button type="button" onClick={() => void handleImport(true)} disabled={isBusy}>Explicit Import</button>
      </div>
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function libraryToolForItem(item: LocalContentLibraryItem): AuthoringToolId {
  if (item.content_type === "world") return "map";
  if (item.content_type === "mod") return "templates";
  if (item.content_type === "template_pack") return "templates";
  if (item.content_type === "scenario_suite") return "scenarios";
  if (item.content_type === "RP_profile") return "rp_characters";
  if (item.content_type === "character_pack") return "rp_characters";
  return "validation";
}

function AuthoringProjectDashboardPanel({
  worldId,
  onOpenEditor
}: {
  worldId: string;
  onOpenEditor: (toolId: AuthoringToolId) => void;
}) {
  const [summary, setSummary] = useState<AuthoringProjectSummary | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadSummary();
  }, [worldId]);

  async function loadSummary() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchAuthoringProjectSummary(worldId);
      setSummary(response);
      setMessage("Project summary refreshed.");
    } catch (err) {
      setSummary(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const countEntries = Object.entries(summary?.content_counts ?? {}).filter(([, value]) => value > 0);
  const packageEntries = Object.entries(summary?.package_status.by_type ?? {});
  const shortcuts: { label: string; tool: AuthoringToolId }[] = [
    { label: "Map", tool: "map" },
    { label: "Quests", tool: "quests" },
    { label: "RP Characters", tool: "rp_characters" },
    { label: "Validation", tool: "validation" },
    { label: "Diff Review", tool: "diff_review" },
    { label: "Library", tool: "library" }
  ];

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Authoring Project Dashboard</h2>
          <p className="muted">World pack, branch, validation, quality, package, and recent edit summary.</p>
        </div>
        <button type="button" onClick={() => void loadSummary()} disabled={isBusy}>Refresh</button>
      </div>
      {summary ? (
        <>
          <div className="template-grid">
            <div className="diff-summary">
              <h3>{summary.active_world_name || summary.active_world || "No world"}</h3>
              <p className="muted">World: {summary.active_world || "none"}</p>
              <p>Branch: {summary.active_branch_name || summary.active_branch || "active world pack"}</p>
            </div>
            <ProjectStatusCard title="Validation" status={summary.validation_status} />
            <ProjectStatusCard title="Quality Gate" status={summary.quality_gate_status} />
            <div className="diff-summary">
              <h3>Packages</h3>
              <p>{summary.package_status.total} local items</p>
              <p className="muted">{packageEntries.map(([type, count]) => `${type}: ${count}`).join(" / ") || "No packages found."}</p>
            </div>
          </div>
          <div className="diff-summary">
            <h3>Content Counts</h3>
            <div className="authoring-section-badges">
              {countEntries.map(([key, value]) => <span key={key} className="badge">{key}: {value}</span>)}
            </div>
          </div>
          <div className="template-grid">
            <div className="diff-summary">
              <h3>Recent Edits</h3>
              {summary.recent_edits.length > 0 ? (
                <ul>
                  {summary.recent_edits.map((edit) => (
                    <li key={`${edit.label}:${edit.updated_at}`}>
                      <code>{edit.label}</code> <span className="muted">{new Date(edit.updated_at).toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              ) : <p className="muted">No recent local edit metadata found.</p>}
            </div>
            <div className="diff-summary">
              <h3>Open Warnings</h3>
              {summary.open_warnings.length > 0 ? (
                <ul>{summary.open_warnings.map((warning) => <li key={warning}><code>{warning}</code></li>)}</ul>
              ) : <p className="muted">No validation warnings.</p>}
            </div>
            <div className="diff-summary">
              <h3>Migration Impact</h3>
              {summary.migration_impact.length > 0 ? (
                <ul>{summary.migration_impact.map((impact) => <li key={impact}><code>{impact}</code></li>)}</ul>
              ) : <p className="muted">No branch migration impact selected.</p>}
            </div>
          </div>
          <div className="authoring-header-actions">
            {shortcuts.map((shortcut) => (
              <button key={shortcut.tool} type="button" onClick={() => onOpenEditor(shortcut.tool)}>
                {shortcut.label}
              </button>
            ))}
          </div>
          {(summary.hidden_details_redacted || summary.sensitive_details_redacted) && (
            <p className="muted">Hidden and sensitive details are redacted from this normal authoring summary.</p>
          )}
        </>
      ) : <EmptyState title="Project summary unavailable." detail="Refresh after selecting a local world pack." />}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ProjectStatusCard({ title, status }: { title: string; status: AuthoringProjectSummary["validation_status"] }) {
  const tone = status.status === "passed" ? "ok" : status.status === "not_run" ? "muted" : "warn";
  return (
    <div className="diff-summary">
      <h3>{title}</h3>
      <p><span className={`badge ${tone}`}>{status.status}</span> {status.summary}</p>
      <p className="muted">Errors: {status.errors} / Warnings: {status.warnings}</p>
      {status.last_run_at && <p className="muted">{new Date(status.last_run_at).toLocaleString()}</p>}
    </div>
  );
}

function ProductionPipelineDashboardPanel({
  worldId,
  onOpenEditor
}: {
  worldId: string;
  onOpenEditor: (toolId: AuthoringToolId) => void;
}) {
  const [summary, setSummary] = useState<ProductionPipelineSummary | null>(null);
  const [error, setError] = useState("");
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    void loadSummary();
  }, [worldId]);

  async function loadSummary() {
    setIsBusy(true);
    setError("");
    try {
      setSummary(await fetchProductionPipelineSummary(worldId));
    } catch (err) {
      setSummary(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Production Pipeline Dashboard</h2>
          <p className="muted">Safe local summary for production drafts, packages, validation, coverage, and quality gates.</p>
        </div>
        <button type="button" onClick={() => void loadSummary()} disabled={isBusy}>Refresh</button>
      </div>
      {summary ? (
        <>
          <div className="template-grid">
            <PipelineStatusCard title="Batch validation" status={summary.batch_validation_status} />
            <PipelineStatusCard title="Quality gate" status={summary.quality_gate_summary} />
            <PipelineStatusCard title="Import/export profiles" status={summary.import_export_profile_status} />
            <PipelineStatusCard title="Script packages" status={summary.script_package_build_status} />
            <PipelineStatusCard title="Campaign starters" status={summary.campaign_starter_status} />
          </div>
          <div className="template-grid">
            <PipelineTaskList title="Production flows" tasks={summary.active_production_drafts} onOpenEditor={onOpenEditor} />
            <PipelineTaskList title="Recent packages" tasks={summary.recent_generated_packages} onOpenEditor={onOpenEditor} />
            <div className="diff-summary">
              <h3>Coverage plan</h3>
              {summary.content_coverage_plan ? (
                <ul className="compact-list">
                  <li>Location gaps: {summary.content_coverage_plan.missing_location_types.length}</li>
                  <li>NPC gaps: {summary.content_coverage_plan.missing_npc_archetypes.length}</li>
                  <li>Quest gaps: {summary.content_coverage_plan.missing_quest_types.length}</li>
                  <li>Scenario gaps: {summary.content_coverage_plan.missing_scenario_regressions.length}</li>
                </ul>
              ) : <p className="muted">No coverage plan available.</p>}
            </div>
          </div>
          <div className="authoring-header-actions">
            {summary.quick_entries.map((entry) => (
              <button key={entry.tool_id} type="button" onClick={() => onOpenEditor(pipelineToolId(entry.tool_id))}>
                {entry.label}
              </button>
            ))}
          </div>
          {(summary.blockers.length > 0 || summary.warnings.length > 0) && (
            <div className="diff-summary">
              <h3>Warnings / blockers</h3>
              <ul className="compact-list">
                {summary.blockers.map((item) => <li key={`b-${item}`} className="error">{item}</li>)}
                {summary.warnings.map((item) => <li key={`w-${item}`}>{item}</li>)}
              </ul>
            </div>
          )}
          <p className="muted">Hidden content, sensitive paths, API keys, and raw environment values are redacted.</p>
        </>
      ) : <EmptyState title="Production pipeline summary unavailable." detail="Refresh after selecting a local world pack." />}
      <ErrorPanel message={error} />
    </section>
  );
}

function PipelineStatusCard({ title, status }: { title: string; status: ProductionPipelineSummary["batch_validation_status"] }) {
  const tone = status.status === "passed" || status.status === "ready" ? "ok" : status.status === "not_run" ? "muted" : "warn";
  return (
    <div className="diff-summary">
      <h3>{title}</h3>
      <p><span className={`badge ${tone}`}>{status.status}</span> {status.summary}</p>
      <p className="muted">Count: {status.count} / Blockers: {status.blockers.length} / Warnings: {status.warnings.length}</p>
    </div>
  );
}

function PipelineTaskList({
  title,
  tasks,
  onOpenEditor
}: {
  title: string;
  tasks: ProductionPipelineTask[];
  onOpenEditor: (toolId: AuthoringToolId) => void;
}) {
  return (
    <div className="diff-summary">
      <h3>{title}</h3>
      {tasks.length > 0 ? (
        <ul className="compact-list">
          {tasks.map((task) => (
            <li key={`${task.tool_id}-${task.label}`}>
              <button type="button" className="link-button" onClick={() => onOpenEditor(pipelineToolId(task.tool_id))}>
                {task.label}
              </button>
              <span className="muted"> {task.summary}</span>
            </li>
          ))}
        </ul>
      ) : <p className="muted">No package artifacts indexed yet.</p>}
    </div>
  );
}

function pipelineToolId(toolId: string): AuthoringToolId {
  if (toolId === "world_pack_wizard") return "world_pack_wizard";
  if (toolId === "npc_pack_generator") return "npc_pack_generator";
  if (toolId === "quest_pack_generator") return "quest_pack_generator";
  if (toolId === "script_package_builder") return "template_wizard";
  if (toolId === "campaign_starter") return "template_wizard";
  if (toolId === "batch_validator") return "validation";
  if (toolId === "scenarios") return "scenarios";
  return "library";
}

function toolForFile(fileName: string): AuthoringToolId {
  if (fileName === "locations.yaml") return "map";
  if (fileName === "quests.yaml") return "quests";
  if (fileName === "npcs.yaml") return "rp_characters";
  if (fileName === "relationships.yaml" || fileName === "factions.yaml") return "social";
  if (fileName === "items.yaml") return "economy";
  if (fileName === "rumors.yaml") return "rumor_crime";
  if (fileName === "dialogue_scenes.yaml") return "dialogue_scenes";
  if (fileName === "group_rp_scenes.yaml") return "group_rp_scenes";
  return "validation";
}

function ScenarioTemplatePanel() {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [rpTemplates, setRPTemplates] = useState<RPScenarioTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [selectedRPTemplateId, setSelectedRPTemplateId] = useState<string>("");
  const [templateTypeFilter, setTemplateTypeFilter] = useState<string>("all");
  const [targetWorldId, setTargetWorldId] = useState<string>("mist_valley");
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<ScenarioTemplatePreviewResponse | null>(null);
  const [rpPreview, setRPPreview] = useState<RPScenarioTemplatePreviewResponse | null>(null);
  const [rpParticipantText, setRPParticipantText] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadTemplates();
  }, []);

  const filteredTemplates =
    templateTypeFilter === "all"
      ? templates
      : templates.filter((template) => template.template_type === templateTypeFilter);
  const selectedTemplate =
    filteredTemplates.find((template) => template.id === selectedTemplateId) ?? filteredTemplates[0] ?? null;
  const selectedRPTemplate = rpTemplates.find((template) => template.id === selectedRPTemplateId) ?? rpTemplates[0] ?? null;

  useEffect(() => {
    if (!selectedTemplate) {
      return;
    }
    setVariables((current) => {
      const next: Record<string, string> = { ...selectedTemplate.optional_variables };
      selectedTemplate.required_variables.forEach((name) => {
        next[name] = current[name] ?? "";
      });
      Object.entries(current).forEach(([key, value]) => {
        if (selectedTemplate.required_variables.includes(key) || key in selectedTemplate.optional_variables) {
          next[key] = value;
        }
      });
      return next;
    });
    setPreview(null);
  }, [selectedTemplate?.id]);

  async function loadTemplates() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchScenarioTemplates();
      const rpResponse = await fetchRPScenarioTemplates();
      setTemplates(response.templates);
      setRPTemplates(rpResponse.templates);
      setSelectedTemplateId((current) => current || response.templates[0]?.id || "");
      setSelectedRPTemplateId((current) => current || rpResponse.templates[0]?.id || "");
    } catch (err) {
      setTemplates([]);
      setRPTemplates([]);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePreviewTemplate() {
    if (!selectedTemplate) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewScenarioTemplate(
        selectedTemplate.id,
        variables,
        selectedTemplate.template_type === "world" ? undefined : targetWorldId
      );
      setPreview(response);
      setMessage(
        response.validation_report?.ok
          ? "Template preview is valid. Rendered files were not written to disk."
          : "Template preview completed with validation issues."
      );
    } catch (err) {
      setPreview(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApplyTemplate() {
    if (!selectedTemplate) {
      return;
    }
    const targetDescription =
      selectedTemplate.template_type === "world"
        ? "a new world pack from the rendered manifest"
        : `world pack '${targetWorldId}'`;
    if (!confirmDangerousAction(`Apply '${selectedTemplate.name}' to ${targetDescription}? This writes local YAML files after validation.`)) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyScenarioTemplate(
        selectedTemplate.id,
        variables,
        selectedTemplate.template_type === "world" ? undefined : targetWorldId
      );
      setPreview(response);
      setMessage(`Template applied to ${response.target_world_id ?? "the target world"} after validation.`);
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const variableNames = selectedTemplate
    ? Array.from(new Set([...selectedTemplate.required_variables, ...Object.keys(selectedTemplate.optional_variables)]))
    : [];
  const rpParticipants = rpParticipantText
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  async function handlePreviewRPTemplate() {
    if (!selectedRPTemplate) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewRPScenarioTemplate(selectedRPTemplate.id, undefined, rpParticipants);
      setRPPreview(response);
      setMessage(response.errors.length ? "RP template preview found blocking issues." : "RP template preview created a safe dialogue draft.");
    } catch (err) {
      setRPPreview(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApplyRPTemplate() {
    if (!selectedRPTemplate) {
      return;
    }
    if (!confirmDangerousAction(`Apply '${selectedRPTemplate.name}' as an RP dialogue draft? This does not modify GameState.`)) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyRPScenarioTemplate(selectedRPTemplate.id, undefined, rpParticipants);
      setRPPreview(response);
      setMessage("RP scenario draft created. Start the actual scene through Dialogue Mode.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Local Template Browser</h2>
          <p className="muted">Browse, preview, validate, and explicitly apply local templates without touching active saves.</p>
        </div>
        <button type="button" onClick={() => void loadTemplates()} disabled={isBusy}>
          Refresh Templates
        </button>
      </div>

      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice api-disabled-notice">Scenario templates require the local authoring API.</div>
      )}

      {templates.length > 0 ? (
        <div className="template-grid">
          <label>
            Type
            <select
              value={templateTypeFilter}
              onChange={(event) => {
                setTemplateTypeFilter(event.target.value);
                setSelectedTemplateId("");
                setPreview(null);
              }}
              disabled={isBusy}
            >
              <option value="all">All template types</option>
              <option value="world">world</option>
              <option value="quest">quest</option>
              <option value="location_cluster">location_cluster</option>
              <option value="npc_set">npc_set</option>
              <option value="faction_set">faction_set</option>
              <option value="mystery">mystery</option>
              <option value="combat_encounter">combat_encounter</option>
            </select>
          </label>
          <label>
            Template
            <select
              value={selectedTemplate?.id ?? ""}
              onChange={(event) => setSelectedTemplateId(event.target.value)}
              disabled={isBusy}
            >
              {filteredTemplates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          <div>
            <p className="muted">{selectedTemplate?.description}</p>
            <span className="badge">{selectedTemplate?.template_type}</span>
            {selectedTemplate?.tags.map((tag) => (
              <span className="chip" key={tag}>{tag}</span>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState title="No templates available." detail="Add local templates under the templates directory." />
      )}

      {selectedTemplate && (
        <div>
          <div className="template-variable-grid">
            {selectedTemplate.template_type !== "world" && (
              <label>
                Target world
                <select value={targetWorldId} onChange={(event) => setTargetWorldId(event.target.value)} disabled={isBusy}>
                  {WORLD_OPTIONS.map((world) => (
                    <option key={world.id} value={world.id}>{world.name}</option>
                  ))}
                </select>
              </label>
            )}
            {variableNames.map((name) => (
              <label key={name}>
                {name}
                <input
                  value={variables[name] ?? ""}
                  onChange={(event) => {
                    setVariables((current) => ({ ...current, [name]: event.target.value }));
                    setPreview(null);
                  }}
                  placeholder={selectedTemplate.required_variables.includes(name) ? "required" : "optional"}
                  disabled={isBusy}
                />
              </label>
            ))}
          </div>
          {selectedTemplate.validation_rules.length > 0 && (
            <div className="notice">
              <strong>Validation rules</strong>
              <ul>
                {selectedTemplate.validation_rules.map((rule) => (
                  <li key={rule}>{rule}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreviewTemplate()} disabled={!selectedTemplate || isBusy}>
          Preview Template
        </button>
        <button
          type="button"
          onClick={() => void handleApplyTemplate()}
          disabled={!selectedTemplate || isBusy}
        >
          Apply Template
        </button>
        {preview && <span className="badge">{preview.writes_to_disk ? "writes files" : "preview only"}</span>}
      </div>

      {preview && (
        <div className="template-preview">
          <h3>Rendered files</h3>
          <div className="chips">
            {preview.rendered.files.map((file) => (
              <span className="chip" key={file.file_name}>
                {file.file_name}
              </span>
            ))}
          </div>
          {preview.validation_report && (
            <div>
              <p className={preview.validation_report.ok ? "muted" : "error"}>
                Validation: {preview.validation_report.ok ? "passed" : `${preview.validation_report.errors.length} errors`}
              </p>
              <ValidationIssueList
                issues={[...preview.validation_report.errors, ...preview.validation_report.warnings]}
                onSelectIssue={() => undefined}
              />
            </div>
          )}
          <AuthoringPreviewCode content={preview.rendered.files[0]?.content || "No rendered content."} />
        </div>
      )}

      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
      <div className="template-preview">
        <h3>RP Scenario Templates</h3>
        <p className="muted">Preview roleplay dialogue drafts. These templates do not write files or modify active saves.</p>
        {rpTemplates.length > 0 ? (
          <div className="template-grid">
            <label>
              RP template
              <select value={selectedRPTemplate?.id ?? ""} onChange={(event) => setSelectedRPTemplateId(event.target.value)} disabled={isBusy}>
                {rpTemplates.map((template) => (
                  <option key={template.id} value={template.id}>{template.name}</option>
                ))}
              </select>
            </label>
            <label>
              Participant override
              <input
                value={rpParticipantText}
                onChange={(event) => setRPParticipantText(event.target.value)}
                placeholder={selectedRPTemplate?.required_participants.join(", ") || "npc ids"}
                disabled={isBusy}
              />
            </label>
            <div>
              <p className="muted">{selectedRPTemplate?.description}</p>
              <span className="badge">{selectedRPTemplate?.scene_type}</span>
              <span className="badge">{selectedRPTemplate?.suggested_dialogue_mode}</span>
              <span className="badge">{selectedRPTemplate?.suggested_mood}</span>
            </div>
          </div>
        ) : (
          <EmptyState title="No RP templates available." detail="Add local RP scenario templates under templates/rp." />
        )}
        {selectedRPTemplate && (
          <div className="notice">
            <strong>Safety notes</strong>
            <ul>
              {selectedRPTemplate.safety_notes.map((note) => <li key={note}>{note}</li>)}
            </ul>
          </div>
        )}
        <div className="authoring-header-actions">
          <button type="button" onClick={() => void handlePreviewRPTemplate()} disabled={!selectedRPTemplate || isBusy}>
            Preview RP Draft
          </button>
          <button type="button" onClick={() => void handleApplyRPTemplate()} disabled={!selectedRPTemplate || isBusy}>
            Apply RP Draft
          </button>
        </div>
        {rpPreview && (
          <div className="authoring-preview-box">
            <h4>Dialogue draft</h4>
            <p><span className="muted">Type</span> {rpPreview.draft.scene_type}</p>
            <p><span className="muted">Participants</span> {rpPreview.draft.participant_ids.join(", ") || "none"}</p>
            <p><span className="muted">Mode</span> {rpPreview.draft.dialogue_mode}</p>
            <p><span className="muted">Mood</span> {rpPreview.draft.scene_mood_preset_id || rpPreview.draft.scene_mood}</p>
            <p><span className="muted">Topics</span> {rpPreview.draft.active_topics.join(", ") || "open"}</p>
            <p className="muted">{rpPreview.draft.opening_context_summary}</p>
            <span className="badge">{rpPreview.writes_to_disk ? "writes disk" : "no disk write"}</span>
            <span className="badge">{rpPreview.modifies_game_state ? "modifies GameState" : "no GameState change"}</span>
            {rpPreview.warnings.length > 0 && <ItemList emptyText="No warnings." items={rpPreview.warnings.map((warning) => <span key={warning}>{warning}</span>)} />}
            {rpPreview.errors.length > 0 && <ItemList emptyText="No errors." items={rpPreview.errors.map((item) => <span key={item}>{item}</span>)} />}
          </div>
        )}
      </div>
    </section>
  );
}

function QuestGraphEditor({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContent: string, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<QuestGraphResponse | null>(null);
  const [selectedQuestId, setSelectedQuestId] = useState<string>("");
  const [selectedStageId, setSelectedStageId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [scenarioDraftJson, setScenarioDraftJson] = useState<string>("");
  const [draggingStageId, setDraggingStageId] = useState<string>("");

  useEffect(() => {
    void loadQuestGraph();
  }, [worldId]);

  const selectedQuest = graph?.quests.find((quest) => quest.id === selectedQuestId) ?? graph?.quests[0] ?? null;
  const selectedStage =
    selectedQuest?.stages.find((stage) => stage.id === selectedStageId) ?? selectedQuest?.stages[0] ?? null;

  useEffect(() => {
    if (!selectedQuest) {
      return;
    }
    setSelectedQuestId((current) => current || selectedQuest.id);
    setSelectedStageId((current) =>
      selectedQuest.stages.some((stage) => stage.id === current)
        ? current
        : selectedQuest.stages[0]?.id ?? ""
    );
  }, [selectedQuest?.id, graph?.quests.length]);

  async function loadQuestGraph() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchQuestGraph(worldId);
      setGraph(response);
      setSelectedQuestId(response.quests[0]?.id ?? "");
      setSelectedStageId(response.quests[0]?.stages[0]?.id ?? "");
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateStage(updater: (stage: QuestStageNode) => QuestStageNode) {
    if (!graph || !selectedQuest || !selectedStage) {
      return;
    }
    setGraph({
      ...graph,
      quests: graph.quests.map((quest) =>
        quest.id === selectedQuest.id
          ? {
              ...quest,
              stages: quest.stages.map((stage) => (stage.id === selectedStage.id ? updater(stage) : stage))
            }
          : quest
      )
    });
  }

  function updateStageCoordinates(stageId: string, x: number, y: number) {
    if (!graph || !selectedQuest) {
      return;
    }
    setGraph({
      ...graph,
      quests: graph.quests.map((quest) =>
        quest.id === selectedQuest.id
          ? {
              ...quest,
              stages: quest.stages.map((stage) => (stage.id === stageId ? { ...stage, x, y } : stage))
            }
          : quest
      )
    });
  }

  function handleStagePointerMove(event: PointerEvent<SVGSVGElement>) {
    if (!draggingStageId) {
      return;
    }
    const rect = event.currentTarget.getBoundingClientRect();
    const point = {
      x: ((event.clientX - rect.left) / Math.max(rect.width, 1)) * 760,
      y: ((event.clientY - rect.top) / Math.max(rect.height, 1)) * 300
    };
    updateStageCoordinates(draggingStageId, point.x, point.y);
  }

  function updateSelectedQuest(updater: (quest: NonNullable<typeof selectedQuest>) => NonNullable<typeof selectedQuest>) {
    if (!graph || !selectedQuest) {
      return;
    }
    setGraph({
      ...graph,
      quests: graph.quests.map((quest) => (quest.id === selectedQuest.id ? updater(quest) : quest))
    });
  }

  function addStage() {
    if (!graph || !selectedQuest) {
      return;
    }
    const baseId = "new_stage";
    const existing = new Set(selectedQuest.stages.map((stage) => stage.id));
    let candidate = baseId;
    let suffix = 1;
    while (existing.has(candidate)) {
      suffix += 1;
      candidate = `${baseId}_${suffix}`;
    }
    updateSelectedQuest((quest) => ({
      ...quest,
      stages: [
        ...quest.stages,
        {
          id: candidate,
          title: "New Stage",
          description: "",
          objectives: [],
          next_stages: [],
          failure_stages: [],
          alternate_stages: [],
          x: 120 + selectedQuest.stages.length * 120,
          y: 120
        }
      ]
    }));
    setSelectedStageId(candidate);
  }

  function deleteSelectedStage() {
    if (!selectedQuest || !selectedStage || selectedQuest.stages.length <= 1) {
      return;
    }
    const confirmed = confirmDangerousAction(`Delete stage "${selectedStage.id}" from this quest graph draft?`);
    if (!confirmed) {
      return;
    }
    updateSelectedQuest((quest) => ({
      ...quest,
      stages: quest.stages
        .filter((stage) => stage.id !== selectedStage.id)
        .map((stage) => ({
          ...stage,
          next_stages: stage.next_stages.filter((id) => id !== selectedStage.id),
          failure_stages: stage.failure_stages.filter((id) => id !== selectedStage.id),
          alternate_stages: stage.alternate_stages.filter((id) => id !== selectedStage.id)
        })),
      initial_stage: quest.initial_stage === selectedStage.id ? quest.stages.find((stage) => stage.id !== selectedStage.id)?.id ?? "" : quest.initial_stage,
      triggers: quest.triggers.map((trigger) => ({
        ...trigger,
        next_stage: trigger.next_stage === selectedStage.id ? null : trigger.next_stage
      }))
    }));
  }

  function setStageId(nextId: string) {
    if (!selectedQuest || !selectedStage) {
      return;
    }
    const cleanId = nextId.trim();
    if (!cleanId) {
      return;
    }
    const previousId = selectedStage.id;
    updateSelectedQuest((quest) => ({
      ...quest,
      initial_stage: quest.initial_stage === previousId ? cleanId : quest.initial_stage,
      stages: quest.stages.map((stage) =>
        stage.id === previousId
          ? { ...stage, id: cleanId }
          : {
              ...stage,
              next_stages: stage.next_stages.map((id) => (id === previousId ? cleanId : id)),
              failure_stages: stage.failure_stages.map((id) => (id === previousId ? cleanId : id)),
              alternate_stages: stage.alternate_stages.map((id) => (id === previousId ? cleanId : id))
            }
      ),
      triggers: quest.triggers.map((trigger) => ({
        ...trigger,
        next_stage: trigger.next_stage === previousId ? cleanId : trigger.next_stage
      }))
    }));
    setSelectedStageId(cleanId);
  }

  function validationIssuesForStage(stageId: string): AuthoringValidation["errors"] {
    const issues = [...(validation?.errors ?? []), ...(validation?.warnings ?? [])];
    return issues.filter((issue) => issue.path.includes(`.${stageId}`) || issue.ref_id === stageId);
  }

  function addQuest() {
    if (!graph) {
      return;
    }
    const existing = new Set(graph.quests.map((quest) => quest.id));
    let candidate = "new_quest";
    let suffix = 1;
    while (existing.has(candidate)) {
      suffix += 1;
      candidate = `new_quest_${suffix}`;
    }
    const quest = {
      id: candidate,
      title: "New Quest",
      description: "",
      initial_stage: "start",
      visibility: "hidden",
      stages: [
        {
          id: "start",
          title: "Start",
          description: "",
          objectives: [],
          next_stages: [],
          failure_stages: [],
          alternate_stages: [],
          x: 120,
          y: 120
        }
      ],
      triggers: [],
      rewards: [],
      consequences: [],
      x: 80,
      y: 80
    };
    setGraph({ ...graph, quests: [...graph.quests, quest] });
    setSelectedQuestId(candidate);
    setSelectedStageId("start");
  }

  function deleteSelectedQuest() {
    if (!graph || !selectedQuest) {
      return;
    }
    const confirmed = confirmDangerousAction(`Delete quest "${selectedQuest.id}" from this quest graph draft?`);
    if (!confirmed) {
      return;
    }
    const quests = graph.quests.filter((quest) => quest.id !== selectedQuest.id);
    setGraph({ ...graph, quests });
    setSelectedQuestId(quests[0]?.id ?? "");
    setSelectedStageId(quests[0]?.stages[0]?.id ?? "");
  }

  function addTrigger() {
    if (!selectedQuest) {
      return;
    }
    const trigger: QuestTriggerNode = {
      type: "npc_talked",
      id: "",
      action: "activate",
      objective_id: null,
      next_stage: selectedStage?.id ?? null,
      x: 120,
      y: 320
    };
    updateSelectedQuest((quest) => ({ ...quest, triggers: [...quest.triggers, trigger] }));
  }

  function addReward() {
    updateSelectedQuest((quest) => ({
      ...quest,
      rewards: [...quest.rewards, { id: "reward", text: "Reward", reward_type: "generic", x: 120, y: 420 }]
    }));
  }

  function addObjective() {
    if (!selectedStage) {
      return;
    }
    updateStage((stage) => ({
      ...stage,
      objectives: [
        ...stage.objectives,
        {
          id: "new_objective",
          text: "new_objective",
          visibility: "public",
          hidden_authoring_note: null,
          x: 120 + stage.objectives.length * 80,
          y: 220
        }
      ]
    }));
  }

  async function handleScenarioDraft() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await generateQuestGraphScenarioDraft(worldId, graph);
      setScenarioDraftJson(JSON.stringify(response.scenario, null, 2));
      setValidation(response.validation);
      setMessage(response.validation.ok ? "Scenario regression draft generated." : "Scenario draft needs review.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGraphPreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewQuestGraph(worldId, graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Quest graph preview is valid." : "Quest graph preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGraphValidate() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateQuestGraph(worldId, graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Quest graph validation passed." : "Quest graph validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleGraphSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateQuestGraph(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_content, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Quest graph has validation errors. Fix them before saving.");
        return;
      }
      if (validationResponse.validation.warnings.length > 0) {
        const confirmed = confirmDangerousAction("Quest graph has validation warnings. Save anyway?");
        if (!confirmed) {
          setMessage("Save cancelled.");
          return;
        }
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Save cancelled.");
        return;
      }
      const response = await saveQuestGraph(worldId, graph, validationResponse.validation.warnings.length > 0);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.saved ? "Quest graph saved to quests.yaml." : "Quest graph was not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Quest Graph</h2>
          <p className="muted">Authoring-only graph view for stages, objectives, triggers, and next-stage edges.</p>
        </div>
        <button type="button" onClick={() => void loadQuestGraph()} disabled={isBusy}>
          Reload Graph
        </button>
        <button type="button" onClick={addQuest} disabled={isBusy || !graph}>
          Add Quest
        </button>
      </div>

      {graph && graph.quests.length > 0 ? (
        <div className="quest-graph-grid">
          <aside className="quest-graph-list">
            {graph.quests.map((quest) => (
              <button
                type="button"
                key={quest.id}
                className={quest.id === selectedQuest?.id ? "selected" : ""}
                onClick={() => {
                  setSelectedQuestId(quest.id);
                  setSelectedStageId(quest.stages[0]?.id ?? "");
                }}
              >
                <span>{quest.title}</span>
                <span className="file-category">{quest.visibility}</span>
              </button>
            ))}
          </aside>

          <section className="quest-graph-detail">
            {selectedQuest && (
              <div className="form-grid">
                <label>
                  Quest title
                  <input
                    value={selectedQuest.title}
                    onChange={(event) => updateSelectedQuest((quest) => ({ ...quest, title: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Quest visibility
                  <select
                    value={selectedQuest.visibility}
                    onChange={(event) => updateSelectedQuest((quest) => ({ ...quest, visibility: event.target.value }))}
                    disabled={isBusy}
                  >
                    <option value="public">public</option>
                    <option value="hidden">hidden</option>
                  </select>
                </label>
                <label>
                  Initial stage
                  <select
                    value={selectedQuest.initial_stage}
                    onChange={(event) => updateSelectedQuest((quest) => ({ ...quest, initial_stage: event.target.value }))}
                    disabled={isBusy}
                  >
                    {selectedQuest.stages.map((stage) => (
                      <option key={stage.id} value={stage.id}>
                        {stage.id}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="full-width">
                  Quest description
                  <textarea
                    value={selectedQuest.description}
                    onChange={(event) => updateSelectedQuest((quest) => ({ ...quest, description: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <div className="full-width">
                  <button type="button" onClick={deleteSelectedQuest} disabled={isBusy || !selectedQuest}>
                    Delete Quest
                  </button>
                </div>
              </div>
            )}
            {selectedQuest && (
              <svg
                className="map-editor-canvas"
                viewBox="0 0 760 300"
                role="img"
                aria-label="Quest stage graph"
                onPointerMove={handleStagePointerMove}
                onPointerUp={() => setDraggingStageId("")}
                onPointerLeave={() => setDraggingStageId("")}
              >
                {selectedQuest.stages.flatMap((stage) =>
                  [...stage.next_stages, ...stage.failure_stages, ...stage.alternate_stages].map((targetId) => {
                    const target = selectedQuest.stages.find((candidate) => candidate.id === targetId);
                    if (!target) {
                      return null;
                    }
                    return (
                      <line
                        key={`${stage.id}-${targetId}`}
                        className={stage.failure_stages.includes(targetId) ? "map-edge locked" : "map-edge"}
                        x1={stage.x || 120}
                        y1={stage.y || 120}
                        x2={target.x || 120}
                        y2={target.y || 120}
                      />
                    );
                  })
                )}
                {selectedQuest.stages.map((stage) => (
                  <g
                    key={stage.id}
                    className="map-node"
                    transform={`translate(${stage.x || 120}, ${stage.y || 120})`}
                    onPointerDown={(event) => {
                      event.currentTarget.setPointerCapture(event.pointerId);
                      setDraggingStageId(stage.id);
                      setSelectedStageId(stage.id);
                    }}
                  >
                    <circle r="24" />
                    <text y="46">{stage.id}</text>
                  </g>
                ))}
              </svg>
            )}
            <div className="quest-stage-pills">
              {selectedQuest?.stages.map((stage) => (
                <button
                  type="button"
                  key={stage.id}
                  className={stage.id === selectedStage?.id ? "selected" : ""}
                  onClick={() => setSelectedStageId(stage.id)}
                >
                  {stage.title}
                </button>
              ))}
              <button type="button" onClick={addStage} disabled={isBusy || !selectedQuest}>
                Add Stage
              </button>
            </div>

            {selectedStage && (
              <div className="form-grid">
                <label>
                  Stage id
                  <input
                    value={selectedStage.id}
                    onChange={(event) => setStageId(event.target.value)}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Stage title
                  <input
                    value={selectedStage.title}
                    onChange={(event) => updateStage((stage) => ({ ...stage, title: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label className="full-width">
                  Stage description
                  <textarea
                    value={selectedStage.description}
                    onChange={(event) => updateStage((stage) => ({ ...stage, description: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label className="full-width">
                  Objectives
                  <div className="button-row">
                    <button type="button" onClick={addObjective} disabled={isBusy}>
                      Add Objective
                    </button>
                  </div>
                </label>
                {selectedStage.objectives.map((objective, objectiveIndex) => (
                  <div className="authoring-preview-box full-width" key={`${selectedStage.id}-${objective.id}-${objectiveIndex}`}>
                    <label>
                      Objective id
                      <input
                        value={objective.id}
                        onChange={(event) =>
                          updateStage((stage) => ({
                            ...stage,
                            objectives: stage.objectives.map((item, itemIndex) =>
                              itemIndex === objectiveIndex ? { ...item, id: event.target.value, text: item.text || event.target.value } : item
                            )
                          }))
                        }
                        disabled={isBusy}
                      />
                    </label>
                    <label>
                      Player text
                      <input
                        value={objective.text}
                        onChange={(event) =>
                          updateStage((stage) => ({
                            ...stage,
                            objectives: stage.objectives.map((item, itemIndex) =>
                              itemIndex === objectiveIndex ? { ...item, text: event.target.value } : item
                            )
                          }))
                        }
                        disabled={isBusy}
                      />
                    </label>
                    <label>
                      Visibility
                      <select
                        value={objective.visibility}
                        onChange={(event) =>
                          updateStage((stage) => ({
                            ...stage,
                            objectives: stage.objectives.map((item, itemIndex) =>
                              itemIndex === objectiveIndex ? { ...item, visibility: event.target.value } : item
                            )
                          }))
                        }
                        disabled={isBusy}
                      >
                        <option value="public">public</option>
                        <option value="hidden">hidden</option>
                      </select>
                    </label>
                    <label>
                      Hidden note
                      <input
                        value={objective.hidden_authoring_note ?? ""}
                        onChange={(event) =>
                          updateStage((stage) => ({
                            ...stage,
                            objectives: stage.objectives.map((item, itemIndex) =>
                              itemIndex === objectiveIndex ? { ...item, hidden_authoring_note: event.target.value || null } : item
                            )
                          }))
                        }
                        disabled={isBusy}
                      />
                    </label>
                  </div>
                ))}
                <label>
                  Next stages
                  <input
                    value={selectedStage.next_stages.join(", ")}
                    onChange={(event) =>
                      updateStage((stage) => ({
                        ...stage,
                        next_stages: event.target.value
                          .split(",")
                          .map((item) => item.trim())
                          .filter(Boolean)
                      }))
                    }
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Failure stages
                  <input
                    value={selectedStage.failure_stages.join(", ")}
                    onChange={(event) =>
                      updateStage((stage) => ({
                        ...stage,
                        failure_stages: splitCsv(event.target.value)
                      }))
                    }
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Alternate stages
                  <input
                    value={selectedStage.alternate_stages.join(", ")}
                    onChange={(event) =>
                      updateStage((stage) => ({
                        ...stage,
                        alternate_stages: splitCsv(event.target.value)
                      }))
                    }
                    disabled={isBusy}
                  />
                </label>
                <div className="full-width">
                  <button type="button" onClick={deleteSelectedStage} disabled={isBusy || !selectedQuest || selectedQuest.stages.length <= 1}>
                    Delete Stage
                  </button>
                  {validationIssuesForStage(selectedStage.id).map((issue) => (
                    <p className={issue.severity === "error" ? "error" : "muted"} key={`${issue.code}-${issue.path}`}>
                      {redactReportText(issue.path)}: {redactReportText(issue.message)}
                    </p>
                  ))}
                </div>
              </div>
            )}

            <section className="studio-section">
              <h3>Edges</h3>
              <ItemList
                emptyText="No graph edges."
                items={(graph?.edges ?? [])
                  .filter((edge) => edge.quest_id === selectedQuest?.id)
                  .map((edge) => (
                    <span key={`${edge.source}-${edge.target}-${edge.type}`}>
                      {edge.source} {"->"} {edge.target} ({edge.type}
                      {edge.label ? ` / ${edge.label}` : ""})
                    </span>
                  ))}
              />
            </section>

            <section className="studio-section">
              <h3>Triggers</h3>
              <button type="button" onClick={addTrigger} disabled={isBusy || !selectedQuest}>
                Add Trigger
              </button>
              {(selectedQuest?.triggers ?? []).length > 0 ? (
                <div className="form-grid">
                  {(selectedQuest?.triggers ?? []).map((trigger, index) => (
                    <div className="authoring-preview-box" key={`${trigger.type}-${trigger.id}-${index}`}>
                      <label>
                        Type
                        <input
                          value={trigger.type}
                          onChange={(event) =>
                            updateSelectedQuest((quest) => ({
                              ...quest,
                              triggers: quest.triggers.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, type: event.target.value } : item
                              )
                            }))
                          }
                          disabled={isBusy}
                        />
                      </label>
                      <label>
                        Ref id
                        <input
                          value={trigger.id}
                          onChange={(event) =>
                            updateSelectedQuest((quest) => ({
                              ...quest,
                              triggers: quest.triggers.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, id: event.target.value } : item
                              )
                            }))
                          }
                          disabled={isBusy}
                        />
                      </label>
                      <label>
                        Action
                        <select
                          value={trigger.action}
                          onChange={(event) =>
                            updateSelectedQuest((quest) => ({
                              ...quest,
                              triggers: quest.triggers.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, action: event.target.value } : item
                              )
                            }))
                          }
                          disabled={isBusy}
                        >
                          <option value="activate">activate</option>
                          <option value="advance">advance</option>
                          <option value="complete_objective">complete_objective</option>
                        </select>
                      </label>
                      <label>
                        Objective id
                        <input
                          value={trigger.objective_id ?? ""}
                          onChange={(event) =>
                            updateSelectedQuest((quest) => ({
                              ...quest,
                              triggers: quest.triggers.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, objective_id: event.target.value || null } : item
                              )
                            }))
                          }
                          disabled={isBusy}
                        />
                      </label>
                      <label>
                        Next stage
                        <input
                          value={trigger.next_stage ?? ""}
                          onChange={(event) =>
                            updateSelectedQuest((quest) => ({
                              ...quest,
                              triggers: quest.triggers.map((item, itemIndex) =>
                                itemIndex === index ? { ...item, next_stage: event.target.value || null } : item
                              )
                            }))
                          }
                          disabled={isBusy}
                        />
                      </label>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No triggers." detail="This quest has no trigger rows yet." />
              )}
            </section>

            <section className="studio-section">
              <h3>Rewards</h3>
              <button type="button" onClick={addReward} disabled={isBusy || !selectedQuest}>
                Add Reward
              </button>
              <textarea
                value={(selectedQuest?.rewards ?? []).map((reward) => `${reward.id}|${reward.text}|${reward.reward_type}`).join("\n")}
                onChange={(event) =>
                  updateSelectedQuest((quest) => ({
                    ...quest,
                    rewards: event.target.value
                      .split("\n")
                      .map((line) => line.trim())
                      .filter(Boolean)
                      .map((line) => {
                        const [id, text, rewardType] = line.split("|");
                        return {
                          id: id?.trim() || "reward",
                          text: text?.trim() || id?.trim() || "reward",
                          reward_type: rewardType?.trim() || "generic",
                          x: 120,
                          y: 420
                        };
                      })
                  }))
                }
                disabled={isBusy}
              />
              <p className="muted">Format: id|player-safe text|type. Rewards are content metadata and do not mutate active GameState.</p>
            </section>

            <div className="button-row">
              <button type="button" onClick={() => void handleGraphPreview()} disabled={!graph || isBusy}>
                Preview YAML
              </button>
              <button type="button" onClick={() => void handleGraphValidate()} disabled={!graph || isBusy}>
                Validate
              </button>
              <button type="button" onClick={() => void handleGraphSave()} disabled={!graph || isBusy}>
                Save Quest Graph
              </button>
              <button type="button" onClick={() => void handleScenarioDraft()} disabled={!graph || isBusy}>
                Generate Scenario Draft
              </button>
            </div>
            {scenarioDraftJson && (
              <section className="studio-section">
                <h3>Scenario Draft</h3>
                <AuthoringPreviewCode content={scenarioDraftJson} />
              </section>
            )}
            <PreviewResultPanel title="Quest Graph Validation" validation={validation} />
          </section>
        </div>
      ) : (
        <EmptyState title="No quest graph available." detail="Load quests.yaml through the authoring API to inspect stages." />
      )}

      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

const NPC_GOAL_STATUSES = ["inactive", "active", "blocked", "completed", "failed"];
const NPC_PLANNING_ACTIONS = [
  "move_to_location",
  "move",
  "talk_to_npc",
  "report_crime",
  "spread_rumor",
  "flee_location",
  "guard_location",
  "rest_if_injured",
  "investigate",
  "attack",
  "flee"
];

function NPCGoalEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContent: string, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<NPCGoalAuthoringGraph | null>(null);
  const [selectedNpcId, setSelectedNpcId] = useState<string>("");
  const [selectedGoalId, setSelectedGoalId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [simulationPresets, setSimulationPresets] = useState<NPCSimulationPreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>("");
  const [presetPreview, setPresetPreview] = useState<string>("");

  useEffect(() => {
    void loadGoalGraph();
    void loadSimulationPresets();
  }, [worldId]);

  const selectedNpc = graph?.npcs.find((npc) => npc.npc_id === selectedNpcId) ?? graph?.npcs[0] ?? null;
  const selectedGoal = selectedNpc?.goals.find((goal) => goal.id === selectedGoalId) ?? selectedNpc?.goals[0] ?? null;

  useEffect(() => {
    if (!selectedNpc) {
      return;
    }
    setSelectedNpcId((current) => current || selectedNpc.npc_id);
    setSelectedGoalId((current) =>
      selectedNpc.goals.some((goal) => goal.id === current) ? current : selectedNpc.goals[0]?.id ?? ""
    );
  }, [selectedNpc?.npc_id, graph?.npcs.length]);

  async function loadGoalGraph() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchNPCGoalGraph(worldId);
      setGraph(response);
      setSelectedNpcId(response.npcs[0]?.npc_id ?? "");
      setSelectedGoalId(response.npcs[0]?.goals[0]?.id ?? "");
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelectedNpc(updater: (npc: NPCGoalAuthoringNode) => NPCGoalAuthoringNode) {
    if (!graph || !selectedNpc) {
      return;
    }
    setGraph({
      ...graph,
      npcs: graph.npcs.map((npc) => (npc.npc_id === selectedNpc.npc_id ? updater(npc) : npc))
    });
  }

  function updateSelectedGoal(updater: (goal: NPCGoalNode) => NPCGoalNode) {
    if (!selectedGoal) {
      return;
    }
    updateSelectedNpc((npc) => ({
      ...npc,
      goals: npc.goals.map((goal) => (goal.id === selectedGoal.id ? updater(goal) : goal))
    }));
  }

  function addGoal() {
    if (!selectedNpc) {
      return;
    }
    const existing = new Set(selectedNpc.goals.map((goal) => goal.id));
    let id = "new_goal";
    let suffix = 1;
    while (existing.has(id)) {
      suffix += 1;
      id = `new_goal_${suffix}`;
    }
    updateSelectedNpc((npc) => ({
      ...npc,
      goals: [
        ...npc.goals,
        {
          id,
          description: "New NPC goal",
          priority: 1,
          status: "inactive",
          conditions: [],
          desired_state: {},
          allowed_actions: [],
          forbidden_actions: []
        }
      ]
    }));
    setSelectedGoalId(id);
  }

  function deleteGoal() {
    if (!selectedGoal) {
      return;
    }
    if (!confirmDangerousAction(`Delete NPC goal "${selectedGoal.id}" from this authoring draft?`)) {
      return;
    }
    updateSelectedNpc((npc) => ({
      ...npc,
      goals: npc.goals.filter((goal) => goal.id !== selectedGoal.id),
      current_goal_id: npc.current_goal_id === selectedGoal.id ? null : npc.current_goal_id
    }));
  }

  function setGoalId(id: string) {
    const cleanId = id.trim();
    if (!cleanId || !selectedGoal) {
      return;
    }
    const previousId = selectedGoal.id;
    updateSelectedNpc((npc) => ({
      ...npc,
      current_goal_id: npc.current_goal_id === previousId ? cleanId : npc.current_goal_id,
      goals: npc.goals.map((goal) => (goal.id === previousId ? { ...goal, id: cleanId } : goal))
    }));
    setSelectedGoalId(cleanId);
  }

  async function handlePreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewNPCGoalGraph(worldId, graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "NPC goal preview is valid." : "NPC goal preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateNPCGoalGraph(worldId, graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "NPC goal validation passed." : "NPC goal validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function loadSimulationPresets() {
    try {
      const response = await fetchNPCSimulationPresets();
      setSimulationPresets(response.presets);
      setSelectedPresetId((current) => current || (response.presets[0]?.id ?? ""));
    } catch {
      setSimulationPresets([]);
      setSelectedPresetId("");
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateNPCGoalGraph(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_content, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("NPC goals have validation errors. Fix them before saving.");
        return;
      }
      if (validationResponse.validation.warnings.length > 0 && !confirmDangerousAction("NPC goals have warnings. Save anyway?")) {
        setMessage("Save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Save cancelled.");
        return;
      }
      const response = await saveNPCGoalGraph(worldId, graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.saved ? "NPC goals saved to npcs.yaml." : "NPC goals were not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePresetPreview() {
    if (!selectedNpc || !selectedPresetId) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewNPCSimulationPreset(worldId, selectedNpc.npc_id, selectedPresetId);
      setValidation(response.validation);
      setPresetPreview(response.applied_fields.join(", "));
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Simulation preset preview is valid." : "Simulation preset preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handlePresetApplyDraft() {
    if (!selectedNpc || !selectedPresetId) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await applyNPCSimulationPresetDraft(worldId, selectedNpc.npc_id, selectedPresetId);
      setGraph(response.graph);
      setValidation(response.validation);
      const refreshedNpc = response.graph.npcs.find((npc) => npc.npc_id === selectedNpc.npc_id);
      setSelectedGoalId(refreshedNpc?.goals[0]?.id ?? "");
      setPresetPreview(response.applied_fields.join(", "));
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(
        response.validation.ok
          ? "Simulation preset applied to this authoring draft. Save NPC Goals to persist it."
          : "Simulation preset draft has validation errors."
      );
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const goalIssues = selectedGoal && validation
    ? [...validation.errors, ...validation.warnings].filter(
        (issue) => issue.path.includes(`.${selectedGoal.id}`) || issue.ref_id === selectedGoal.id
      )
    : [];

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>NPC Goal Editor</h2>
          <p className="muted">Authoring-only editor for deterministic NPC goals and planning constraints.</p>
        </div>
        <button type="button" onClick={() => void loadGoalGraph()} disabled={isBusy}>
          Reload Goals
        </button>
      </div>

      {graph && graph.npcs.length > 0 ? (
        <div className="quest-graph-grid">
          <aside className="quest-graph-list">
            {graph.npcs.map((npc) => (
              <button
                type="button"
                key={npc.npc_id}
                className={npc.npc_id === selectedNpc?.npc_id ? "selected" : ""}
                onClick={() => {
                  setSelectedNpcId(npc.npc_id);
                  setSelectedGoalId(npc.goals[0]?.id ?? "");
                }}
              >
                <span>{npc.name}</span>
                <span className="file-category">{npc.goals.length} goals{npc.hidden ? " / hidden" : ""}</span>
              </button>
            ))}
          </aside>

          <section className="quest-graph-detail">
            {selectedNpc && (
              <>
                <section className="authoring-card">
                  <h3>Simulation Preset</h3>
                  <div className="form-grid">
                    <label>
                      Preset
                      <select
                        value={selectedPresetId}
                        onChange={(event) => setSelectedPresetId(event.target.value)}
                        disabled={isBusy || simulationPresets.length === 0}
                      >
                        {simulationPresets.map((preset) => (
                          <option key={preset.id} value={preset.id}>
                            {preset.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Impact
                      <input value={presetPreview || "goals, priorities, duties, disposition"} readOnly />
                    </label>
                  </div>
                  <div className="authoring-actions">
                    <button type="button" onClick={() => void handlePresetPreview()} disabled={isBusy || !selectedPresetId}>
                      Preview Preset
                    </button>
                    <button type="button" onClick={() => void handlePresetApplyDraft()} disabled={isBusy || !selectedPresetId}>
                      Apply to Draft
                    </button>
                  </div>
                </section>
                <div className="quest-stage-pills">
                  {selectedNpc.goals.map((goal) => (
                    <button
                      type="button"
                      key={goal.id}
                      className={goal.id === selectedGoal?.id ? "selected" : ""}
                      onClick={() => setSelectedGoalId(goal.id)}
                    >
                      {goal.id}
                    </button>
                  ))}
                  <button type="button" onClick={addGoal} disabled={isBusy}>
                    Add Goal
                  </button>
                </div>
                <div className="form-grid">
                  <label>
                    Current goal
                    <select
                      value={selectedNpc.current_goal_id ?? ""}
                      onChange={(event) => updateSelectedNpc((npc) => ({ ...npc, current_goal_id: event.target.value || null }))}
                      disabled={isBusy}
                    >
                      <option value="">Unset</option>
                      {selectedNpc.goals.map((goal) => (
                        <option key={goal.id} value={goal.id}>
                          {goal.id}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Constraints
                    <input
                      value={selectedNpc.constraints.join(", ")}
                      onChange={(event) => updateSelectedNpc((npc) => ({ ...npc, constraints: splitCsv(event.target.value) }))}
                      disabled={isBusy}
                    />
                  </label>
                </div>
              </>
            )}

            {selectedGoal ? (
              <div className="form-grid">
                <label>
                  Goal id
                  <input value={selectedGoal.id} onChange={(event) => setGoalId(event.target.value)} disabled={isBusy} />
                </label>
                <label>
                  Status
                  <select
                    value={selectedGoal.status}
                    onChange={(event) => updateSelectedGoal((goal) => ({ ...goal, status: event.target.value }))}
                    disabled={isBusy}
                  >
                    {NPC_GOAL_STATUSES.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Priority
                  <input
                    type="number"
                    min="0"
                    value={selectedGoal.priority}
                    onChange={(event) => updateSelectedGoal((goal) => ({ ...goal, priority: Number(event.target.value) }))}
                    disabled={isBusy}
                  />
                </label>
                <label className="full-width">
                  Description
                  <textarea
                    value={selectedGoal.description}
                    onChange={(event) => updateSelectedGoal((goal) => ({ ...goal, description: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label className="full-width">
                  Conditions, one per line
                  <textarea
                    value={selectedGoal.conditions.join("\n")}
                    onChange={(event) =>
                      updateSelectedGoal((goal) => ({
                        ...goal,
                        conditions: event.target.value.split("\n").map((line) => line.trim()).filter(Boolean)
                      }))
                    }
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Allowed actions
                  <select
                    multiple
                    value={selectedGoal.allowed_actions}
                    onChange={(event) =>
                      updateSelectedGoal((goal) => ({
                        ...goal,
                        allowed_actions: Array.from(event.currentTarget.selectedOptions).map((option) => option.value)
                      }))
                    }
                    disabled={isBusy}
                  >
                    {NPC_PLANNING_ACTIONS.map((action) => (
                      <option key={action} value={action}>
                        {action}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Forbidden actions
                  <select
                    multiple
                    value={selectedGoal.forbidden_actions}
                    onChange={(event) =>
                      updateSelectedGoal((goal) => ({
                        ...goal,
                        forbidden_actions: Array.from(event.currentTarget.selectedOptions).map((option) => option.value)
                      }))
                    }
                    disabled={isBusy}
                  >
                    {NPC_PLANNING_ACTIONS.map((action) => (
                      <option key={action} value={action}>
                        {action}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="full-width">
                  Desired state JSON
                  <textarea
                    value={JSON.stringify(selectedGoal.desired_state, null, 2)}
                    onChange={(event) => {
                      try {
                        const parsed = JSON.parse(event.target.value) as Record<string, unknown>;
                        updateSelectedGoal((goal) => ({ ...goal, desired_state: parsed }));
                      } catch {
                        setMessage("Desired state must be valid JSON before preview/save.");
                      }
                    }}
                    disabled={isBusy}
                  />
                </label>
                <div className="full-width">
                  <button type="button" onClick={deleteGoal} disabled={isBusy}>
                    Delete Goal
                  </button>
                  {goalIssues.map((issue) => (
                    <p className={issue.severity === "error" ? "error" : "muted"} key={`${issue.code}-${issue.path}`}>
                      {redactReportText(issue.path)}: {redactReportText(issue.message)}
                    </p>
                  ))}
                </div>
              </div>
            ) : (
              <EmptyState title="No goal selected." detail="Choose an NPC and add a goal to edit planning behavior." />
            )}

            <AuthoringActionBar
              onPreview={() => void handlePreview()}
              onValidate={() => void handleValidate()}
              onSave={() => void handleSave()}
              disabled={!graph || isBusy}
              previewLabel="Preview YAML"
              saveLabel="Save NPC Goals"
            />
            <PreviewResultPanel title="NPC Goal Validation" validation={validation} />
          </section>
        </div>
      ) : (
        <EmptyState title="No NPC goals available." detail="Load npcs.yaml through the authoring API to edit goals." />
      )}

      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ItemEconomyEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContents: Record<string, string>, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<ItemEconomyAuthoring | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string>("");
  const [selectedMerchantId, setSelectedMerchantId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<"table" | "graph">("table");

  useEffect(() => {
    void loadEconomyGraph();
  }, [worldId]);

  async function loadEconomyGraph() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchItemEconomyAuthoring(worldId);
      setGraph(response);
      setSelectedItemId(response.items[0]?.id ?? "");
      setSelectedMerchantId(response.merchants[0]?.npc_id ?? "");
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelectedItem(updater: (item: ItemEconomyItem) => ItemEconomyItem) {
    if (!graph || !selectedItemId) {
      return;
    }
    setGraph({
      ...graph,
      items: graph.items.map((item) => (item.id === selectedItemId ? updater(item) : item))
    });
  }

  function updateSelectedMerchant(updater: (merchant: MerchantEconomyNode) => MerchantEconomyNode) {
    if (!graph || !selectedMerchantId) {
      return;
    }
    setGraph({
      ...graph,
      merchants: graph.merchants.map((merchant) =>
        merchant.npc_id === selectedMerchantId ? updater(merchant) : merchant
      )
    });
  }

  function addItem() {
    if (!graph) {
      return;
    }
    const id = nextUniqueId(
      "new_item",
      graph.items.map((item) => item.id)
    );
    const item: ItemEconomyItem = {
      id,
      name: "New Item",
      description: "",
      location_id: "village_square",
      owner_id: null,
      container_id: null,
      portable: true,
      visible: true,
      hidden: false,
      discoverable: false,
      discovered_by: [],
      tags: [],
      base_price: 0,
      tradeable: true,
      rarity: "common",
      locked: false,
      lock_difficulty: 0,
      lock_state: "intact",
      stolen_item_policy: "refuse_stolen"
    };
    setGraph({ ...graph, items: [...graph.items, item] });
    setSelectedItemId(id);
  }

  function deleteSelectedItem() {
    if (!graph || !selectedItemId) {
      return;
    }
    if (!confirmDangerousAction(`Delete item "${selectedItemId}" from this authoring draft?`)) {
      return;
    }
    const nextItems = graph.items.filter((item) => item.id !== selectedItemId);
    setGraph({
      ...graph,
      items: nextItems,
      merchants: graph.merchants.map((merchant) => ({
        ...merchant,
        shop_inventory: merchant.shop_inventory.filter((itemId) => itemId !== selectedItemId)
      }))
    });
    setSelectedItemId(nextItems[0]?.id ?? "");
  }

  async function handlePreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewItemEconomyAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Item/economy preview is valid." : "Item/economy preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateItemEconomyAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Item/economy validation passed." : "Item/economy validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleBalanceCheck() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await balanceCheckItemEconomyAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.graph.balance_warnings.length ? "Economy balance warnings found." : "Economy balance check passed.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateItemEconomyAuthoring(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_contents, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Item/economy save blocked by validation errors.");
        return;
      }
      if (
        validationResponse.confirmation_required &&
        !confirmDangerousAction("Validation returned warnings. Save item/economy changes anyway?")
      ) {
        setMessage("Item/economy save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Item/economy save cancelled.");
        return;
      }
      const response = await saveItemEconomyAuthoring(worldId, graph, validationResponse.confirmation_required);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.saved ? "Item/economy data saved." : "Item/economy data was not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selectedItem = graph?.items.find((item) => item.id === selectedItemId) ?? null;
  const selectedMerchant = graph?.merchants.find((merchant) => merchant.npc_id === selectedMerchantId) ?? null;
  const selectedMerchantEdges =
    graph && selectedMerchant
      ? graph.shop_inventory_edges.filter((edge) => edge.merchant_id === selectedMerchant.npc_id)
      : [];
  const visibleShopItems =
    graph && selectedMerchant
      ? selectedMerchant.shop_inventory
          .map((itemId) => graph.items.find((item) => item.id === itemId))
          .filter((item): item is ItemEconomyItem => Boolean(item && item.visible && !item.hidden && item.tradeable))
      : [];

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Item / Economy Editor</h2>
          <p className="muted">Authoring-only editor for item ownership, backend price previews, trade flags, and merchant inventory.</p>
        </div>
        <div className="segmented-control">
          <button type="button" className={viewMode === "table" ? "active" : ""} onClick={() => setViewMode("table")}>Table</button>
          <button type="button" className={viewMode === "graph" ? "active" : ""} onClick={() => setViewMode("graph")}>Graph</button>
          <button type="button" onClick={() => void loadEconomyGraph()} disabled={isBusy}>Reload Economy</button>
        </div>
      </div>

      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Items</h3>
            {graph.items.map((item) => (
              <button
                type="button"
                key={item.id}
                className={item.id === selectedItemId ? "active" : ""}
                onClick={() => setSelectedItemId(item.id)}
              >
                {item.name || item.id}
              </button>
            ))}
            <button type="button" onClick={addItem} disabled={isBusy}>
              Add Item
            </button>
            <h3>Merchants</h3>
            {graph.merchants.map((merchant) => (
              <button
                type="button"
                key={merchant.npc_id}
                className={merchant.npc_id === selectedMerchantId ? "active" : ""}
                onClick={() => setSelectedMerchantId(merchant.npc_id)}
              >
                {merchant.name || merchant.npc_id}
              </button>
            ))}
          </aside>

          <div className="graph-detail-panel">
            {viewMode === "graph" && graph && (
              <ItemEconomyGraphView
                items={graph.items}
                merchants={graph.merchants}
                edges={graph.shop_inventory_edges}
                onSelectItem={setSelectedItemId}
                onSelectMerchant={setSelectedMerchantId}
              />
            )}
            {selectedItem ? (
              <section className="authoring-preview-box">
                <div className="authoring-pane-header compact">
                  <h3>Item Fields</h3>
                  <button type="button" onClick={deleteSelectedItem} disabled={isBusy}>
                    Delete Item
                  </button>
                </div>
                <div className="form-grid">
                  <TextInput label="Id" value={selectedItem.id} onChange={(value) => updateSelectedItem((item) => ({ ...item, id: value }))} />
                  <TextInput label="Name" value={selectedItem.name} onChange={(value) => updateSelectedItem((item) => ({ ...item, name: value }))} />
                  <TextInput label="Rarity" value={selectedItem.rarity} onChange={(value) => updateSelectedItem((item) => ({ ...item, rarity: value }))} />
                  <NumberInput label="Base price" value={selectedItem.base_price} onChange={(value) => updateSelectedItem((item) => ({ ...item, base_price: value }))} />
                  <TextInput label="Stolen policy" value={selectedItem.stolen_item_policy} onChange={(value) => updateSelectedItem((item) => ({ ...item, stolen_item_policy: value }))} />
                  <TextInput label="Location" value={selectedItem.location_id ?? ""} onChange={(value) => updateSelectedItem((item) => ({ ...item, location_id: emptyToNull(value) }))} />
                  <TextInput label="Owner" value={selectedItem.owner_id ?? ""} onChange={(value) => updateSelectedItem((item) => ({ ...item, owner_id: emptyToNull(value) }))} />
                  <TextInput label="Container" value={selectedItem.container_id ?? ""} onChange={(value) => updateSelectedItem((item) => ({ ...item, container_id: emptyToNull(value) }))} />
                  <TextInput label="Tags" value={selectedItem.tags.join(", ")} onChange={(value) => updateSelectedItem((item) => ({ ...item, tags: commaList(value) }))} />
                </div>
                <label>
                  Description
                  <textarea
                    value={selectedItem.description}
                    onChange={(event) => updateSelectedItem((item) => ({ ...item, description: event.target.value }))}
                  />
                </label>
                <div className="checkbox-grid">
                  <label><input type="checkbox" checked={selectedItem.tradeable} onChange={(event) => updateSelectedItem((item) => ({ ...item, tradeable: event.target.checked }))} /> Tradeable</label>
                  <label><input type="checkbox" checked={selectedItem.portable} onChange={(event) => updateSelectedItem((item) => ({ ...item, portable: event.target.checked }))} /> Portable</label>
                  <label><input type="checkbox" checked={selectedItem.hidden} onChange={(event) => updateSelectedItem((item) => ({ ...item, hidden: event.target.checked }))} /> Hidden</label>
                  <label><input type="checkbox" checked={selectedItem.visible} onChange={(event) => updateSelectedItem((item) => ({ ...item, visible: event.target.checked }))} /> Visible</label>
                </div>
              </section>
            ) : (
              <EmptyState title="No item selected." detail="Select or add an item to edit economy fields." />
            )}

            {selectedMerchant && (
              <section className="authoring-preview-box">
                <h3>Merchant Inventory</h3>
                <div className="form-grid">
                  <TextInput label="Merchant NPC" value={selectedMerchant.npc_id} onChange={(value) => updateSelectedMerchant((merchant) => ({ ...merchant, npc_id: value }))} />
                  <NumberInput label="Buy modifier" value={selectedMerchant.buy_price_modifier} onChange={(value) => updateSelectedMerchant((merchant) => ({ ...merchant, buy_price_modifier: value }))} />
                  <NumberInput label="Sell modifier" value={selectedMerchant.sell_price_modifier} onChange={(value) => updateSelectedMerchant((merchant) => ({ ...merchant, sell_price_modifier: value }))} />
                  <TextInput label="Shop inventory" value={selectedMerchant.shop_inventory.join(", ")} onChange={(value) => updateSelectedMerchant((merchant) => ({ ...merchant, shop_inventory: commaList(value) }))} />
                </div>
                <label><input type="checkbox" checked={selectedMerchant.merchant} onChange={(event) => updateSelectedMerchant((merchant) => ({ ...merchant, merchant: event.target.checked }))} /> Merchant enabled</label>
                <h4>Visible shop preview</h4>
                {selectedMerchantEdges.length ? (
                  <ul className="compact-list">
                    {selectedMerchantEdges.map((edge) => {
                      const item = graph.items.find((candidate) => candidate.id === edge.item_id);
                      return item && edge.player_visible ? (
                      <li key={edge.id}>
                          {item.name} buy {edge.buy_price} / sell {edge.sell_price}
                      </li>
                      ) : null;
                    })}
                  </ul>
                ) : (
                  <p className="muted">No player-visible tradeable items. Hidden items remain filtered from player shop UI.</p>
                )}
                {graph.balance_warnings.length > 0 && (
                  <div className="authoring-preview-box subtle">
                    <h4>Balance warnings</h4>
                    <ul className="compact-list">
                      {graph.balance_warnings.map((warning) => (
                        <li key={`${warning.path}:${warning.code}`}>{warning.code}: {warning.message}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </section>
            )}

            <AuthoringActionBar
              onPreview={() => void handlePreview()}
              onValidate={() => void handleValidate()}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <button type="button" onClick={() => void handleBalanceCheck()} disabled={isBusy}>
              Balance Check
            </button>
            <PreviewResultPanel title="Item / Economy Validation" validation={validation} />
          </div>
        </div>
      ) : (
        <EmptyState title="No item/economy graph loaded." detail="Load items.yaml through the authoring API to edit prices and shops." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ItemEconomyGraphView({
  items,
  merchants,
  edges,
  onSelectItem,
  onSelectMerchant
}: {
  items: ItemEconomyItem[];
  merchants: MerchantEconomyNode[];
  edges: ShopInventoryEdge[];
  onSelectItem: (itemId: string) => void;
  onSelectMerchant: (merchantId: string) => void;
}) {
  return (
    <section className="authoring-preview-box">
      <h3>Economy Graph</h3>
      <div className="relationship-grid">
        <div>
          <h4>Merchants</h4>
          <ul className="compact-list">
            {merchants.map((merchant) => (
              <li key={merchant.npc_id}>
                <button type="button" onClick={() => onSelectMerchant(merchant.npc_id)}>
                  {merchant.name || merchant.npc_id}
                </button>
                <span className="muted"> buy {merchant.buy_price_modifier} / sell {merchant.sell_price_modifier}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4>Shop Links</h4>
          <ul className="compact-list">
            {edges.map((edge) => {
              const item = items.find((candidate) => candidate.id === edge.item_id);
              return (
                <li key={edge.id}>
                  <button type="button" onClick={() => onSelectMerchant(edge.merchant_id)}>{edge.merchant_id}</button>
                  {" -> "}
                  <button type="button" onClick={() => onSelectItem(edge.item_id)}>{item?.name ?? edge.item_id}</button>
                  <span className={edge.player_visible ? "muted" : "danger-text"}>
                    {" "}buy {edge.buy_price} / sell {edge.sell_price}{edge.player_visible ? "" : " hidden"}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </section>
  );
}

function TextInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <input type="text" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

const EMPTY_REFERENCE_INDEX: ReferenceIndex = { local_only: true, world_id: "", items: [] };

function useReferenceIndex(worldId: string): ReferenceIndex {
  const [index, setIndex] = useState<ReferenceIndex>(EMPTY_REFERENCE_INDEX);

  useEffect(() => {
    let cancelled = false;
    if (!worldId) {
      setIndex(EMPTY_REFERENCE_INDEX);
      return;
    }
    fetchReferenceIndex(worldId)
      .then((response) => {
        if (!cancelled) {
          setIndex(response);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setIndex(EMPTY_REFERENCE_INDEX);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [worldId]);

  return index;
}

function ReferencePicker({
  label,
  value,
  kind,
  index,
  onChange,
  allowEmpty = true,
  disabled = false
}: {
  label: string;
  value: string;
  kind: ReferenceKind;
  index: ReferenceIndex;
  onChange: (value: string) => void;
  allowEmpty?: boolean;
  disabled?: boolean;
}) {
  const options = index.items.filter((item) => item.kind === kind);
  const selected = options.find((item) => item.id === value) ?? null;
  return (
    <label>
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled || options.length === 0}>
        {allowEmpty && <option value="">None</option>}
        {options.map((item) => (
          <option key={`${item.kind}:${item.id}`} value={item.id}>
            {referenceLabel(item)}
          </option>
        ))}
        {value && !selected && <option value={value}>{value} (missing)</option>}
      </select>
    </label>
  );
}

function referenceLabel(item: ReferenceIndexItem): string {
  const flags = [item.hidden ? "hidden" : "", item.player_visible ? "player" : ""].filter(Boolean).join(", ");
  return `${item.label || item.id} [${item.id}]${flags ? ` (${flags})` : ""}`;
}

function NumberInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        value={Number.isFinite(value) ? value : 0}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function commaList(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function emptyToNull(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function nextUniqueId(prefix: string, existingIds: string[]): string {
  const existing = new Set(existingIds);
  if (!existing.has(prefix)) {
    return prefix;
  }
  let index = 2;
  while (existing.has(`${prefix}_${index}`)) {
    index += 1;
  }
  return `${prefix}_${index}`;
}

function RumorCrimeConsequenceEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContents: Record<string, string>, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<RumorCrimeConsequenceAuthoring | null>(null);
  const [selectedRumorId, setSelectedRumorId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadConsequenceGraph();
  }, [worldId]);

  async function loadConsequenceGraph() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchRumorCrimeAuthoring(worldId);
      setGraph(response);
      setSelectedRumorId(response.rumors[0]?.id ?? "");
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateSelectedRumor(updater: (rumor: RumorAuthoringNode) => RumorAuthoringNode) {
    if (!graph || !selectedRumorId) {
      return;
    }
    setGraph({
      ...graph,
      rumors: graph.rumors.map((rumor) => (rumor.id === selectedRumorId ? updater(rumor) : rumor))
    });
  }

  function addRumor() {
    if (!graph) {
      return;
    }
    const id = nextUniqueId(
      "new_rumor",
      graph.rumors.map((rumor) => rumor.id)
    );
    const rumor: RumorAuthoringNode = {
      id,
      fact_id: null,
      source_event_id: null,
      text_for_player: "",
      truth_status: "unknown",
      known_by_npcs: [],
      known_by_factions: [],
      known_by_player: false,
      spread_level: 0,
      created_turn: 0,
      tags: [],
      delay_turns: 0,
      cooldown_turns: 0,
      dedupe_key: `rumor:${id}`
    };
    setGraph({ ...graph, rumors: [...graph.rumors, rumor] });
    setSelectedRumorId(id);
  }

  function deleteSelectedRumor() {
    if (!graph || !selectedRumorId) {
      return;
    }
    if (!confirmDangerousAction(`Delete rumor "${selectedRumorId}" from this authoring draft?`)) {
      return;
    }
    const nextRumors = graph.rumors.filter((rumor) => rumor.id !== selectedRumorId);
    setGraph({
      ...graph,
      rumors: nextRumors,
      edges: graph.edges.filter((edge) => edge.source !== selectedRumorId && edge.target !== selectedRumorId)
    });
    setSelectedRumorId(nextRumors[0]?.id ?? "");
  }

  async function handlePreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewRumorCrimeAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Consequence preview is valid." : "Consequence preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateRumorCrimeAuthoring(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Consequence validation passed." : "Consequence validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSave() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateRumorCrimeAuthoring(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_contents, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Consequence save blocked by validation errors.");
        return;
      }
      if (
        validationResponse.confirmation_required &&
        !confirmDangerousAction("Validation returned warnings. Save rumor/consequence changes anyway?")
      ) {
        setMessage("Consequence save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Consequence save cancelled.");
        return;
      }
      const response = await saveRumorCrimeAuthoring(worldId, graph, validationResponse.validation.warnings.length > 0);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.saved ? "Rumors saved." : "Rumors were not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selectedRumor = graph?.rumors.find((rumor) => rumor.id === selectedRumorId) ?? null;
  const selectedFact = selectedRumor?.fact_id
    ? graph?.facts.find((fact) => fact.id === selectedRumor.fact_id)
    : null;

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Rumor / Crime Consequence Editor</h2>
          <p className="muted">Authoring-only consequence graph for rumors, crime templates, reputation effects, and quest links.</p>
        </div>
        <button type="button" onClick={() => void loadConsequenceGraph()} disabled={isBusy}>
          Reload Consequences
        </button>
      </div>

      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Rumors</h3>
            {graph.rumors.map((rumor) => (
              <button
                type="button"
                key={rumor.id}
                className={rumor.id === selectedRumorId ? "active" : ""}
                onClick={() => setSelectedRumorId(rumor.id)}
              >
                {rumor.id}
              </button>
            ))}
            <button type="button" onClick={addRumor} disabled={isBusy}>
              Add Rumor
            </button>
          </aside>

          <div className="graph-detail-panel">
            {selectedRumor ? (
              <section className="authoring-preview-box">
                <div className="authoring-pane-header compact">
                  <h3>Rumor Node</h3>
                  <button type="button" onClick={deleteSelectedRumor} disabled={isBusy}>
                    Delete Rumor
                  </button>
                </div>
                <div className="form-grid">
                  <TextInput label="Id" value={selectedRumor.id} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, id: value }))} />
                  <TextInput label="Fact id" value={selectedRumor.fact_id ?? ""} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, fact_id: emptyToNull(value) }))} />
                  <TextInput label="Truth status" value={selectedRumor.truth_status} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, truth_status: value }))} />
                  <NumberInput label="Spread level" value={selectedRumor.spread_level} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, spread_level: value }))} />
                  <NumberInput label="Delay turns" value={selectedRumor.delay_turns} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, delay_turns: value }))} />
                  <NumberInput label="Cooldown turns" value={selectedRumor.cooldown_turns} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, cooldown_turns: value }))} />
                  <TextInput label="Dedupe key" value={selectedRumor.dedupe_key ?? ""} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, dedupe_key: emptyToNull(value) }))} />
                  <TextInput label="Known by NPCs" value={selectedRumor.known_by_npcs.join(", ")} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, known_by_npcs: commaList(value) }))} />
                  <TextInput label="Known by factions" value={selectedRumor.known_by_factions.join(", ")} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, known_by_factions: commaList(value) }))} />
                  <TextInput label="Tags" value={selectedRumor.tags.join(", ")} onChange={(value) => updateSelectedRumor((rumor) => ({ ...rumor, tags: commaList(value) }))} />
                </div>
                <label>
                  Player-facing rumor text
                  <textarea
                    value={selectedRumor.text_for_player ?? ""}
                    onChange={(event) => updateSelectedRumor((rumor) => ({ ...rumor, text_for_player: event.target.value }))}
                  />
                </label>
                <label>
                  <input
                    type="checkbox"
                    checked={selectedRumor.known_by_player}
                    onChange={(event) => updateSelectedRumor((rumor) => ({ ...rumor, known_by_player: event.target.checked }))}
                  />
                  Known by player
                </label>
                {selectedFact?.visibility === "hidden" && (
                  <div className="notice warning">
                    Linked fact is hidden. Keep player-facing rumor text vague; validation warns if it copies hidden text.
                  </div>
                )}
              </section>
            ) : (
              <EmptyState title="No rumor selected." detail="Select or add a rumor to edit consequence text and spread." />
            )}

            <section className="authoring-preview-box">
              <h3>Consequence Graph</h3>
              <div className="compact-grid">
                <DashboardCard title="Triggers" value={String(graph.trigger_nodes.length)}>
                  <p>Event, crime, and rumor trigger entry points.</p>
                </DashboardCard>
                <DashboardCard title="Witnesses" value={String(graph.witness_nodes.length)}>
                  <p>Witness paths derived from known NPCs.</p>
                </DashboardCard>
                <DashboardCard title="Crimes" value={String(graph.crimes.length)}>
                  <p>Derived crime consequence templates.</p>
                </DashboardCard>
                <DashboardCard title="Reputation effects" value={String(graph.reputation_effects.length)}>
                  <p>Faction links from rumor reach.</p>
                </DashboardCard>
                <DashboardCard title="Quest triggers" value={String(graph.quest_triggers.length)}>
                  <p>Quest trigger references related to facts.</p>
                </DashboardCard>
                <DashboardCard title="NPC reactions" value={String(graph.npc_reactions.length)}>
                  <p>NPC reaction effects linked to rumors.</p>
                </DashboardCard>
              </div>
              <p className="muted">
                Impact: {Object.entries(graph.impact_summary).map(([key, value]) => `${key} ${value}`).join(" / ") || "No impact yet"}
              </p>
              {graph.edges.length ? (
                <ul className="compact-list">
                  {graph.edges.map((edge, index) => (
                    <li key={`${edge.source}-${edge.target}-${index}`}>
                      <code>{edge.source}</code> {"->"} <code>{edge.target}</code> 路 {edge.type}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">No derived consequence edges yet.</p>
              )}
            </section>

            <AuthoringActionBar
              onPreview={() => void handlePreview()}
              onValidate={() => void handleValidate()}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <PreviewResultPanel title="Rumor / Crime Validation" validation={validation} />
          </div>
        </div>
      ) : (
        <EmptyState title="No consequence graph loaded." detail="Load rumors.yaml through the authoring API to edit social consequences." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ValidationGraphPanel({
  worldId,
  onSelectIssue
}: {
  worldId: string;
  onSelectIssue: (issue: ValidationGraph["issues"][number]) => void;
}) {
  const [graph, setGraph] = useState<ValidationGraph | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  async function loadGraph() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchValidationGraph(worldId);
      setGraph(response);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const visibleIssues =
    graph?.issues.filter((issue) => severityFilter === "all" || issue.severity === severityFilter) ?? [];
  const issueNodeIds = new Set(visibleIssues.map((issue) => issue.id));
  const visibleEdges = graph?.edges.filter((edge) => issueNodeIds.has(edge.source) || issueNodeIds.has(edge.target)) ?? [];

  return (
    <section className="quest-graph-editor authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Validation Graph</h2>
          <p className="muted">Authoring-only graph of files, references, and validation issues.</p>
        </div>
        <div className="button-row">
          <select value={severityFilter} onChange={(event) => setSeverityFilter(event.target.value)}>
            <option value="all">All severities</option>
            <option value="error">Errors</option>
            <option value="warning">Warnings</option>
            <option value="suggestion">Suggestions</option>
          </select>
          <button type="button" onClick={() => void loadGraph()} disabled={isBusy}>
            Build Graph
          </button>
        </div>
      </div>

      {graph ? (
        <div className="graph-editor-layout">
          <aside className="graph-node-list">
            <h3>Issue Nodes</h3>
            {visibleIssues.length ? (
              visibleIssues.map((issue) => (
                <button type="button" key={issue.id} onClick={() => onSelectIssue(issue)}>
                  {issue.severity}: {issue.code}
                  <small>{issue.file} 路 {issue.path}</small>
                </button>
              ))
            ) : (
              <EmptyState title="No issues for this filter." />
            )}
          </aside>
          <div className="graph-detail-panel">
            <div className="compact-grid">
              <DashboardCard title="Nodes" value={String(graph.nodes.length)}>
                <p>files, entities, references, schema and issues</p>
              </DashboardCard>
              <DashboardCard title="Edges" value={String(graph.edges.length)}>
                <p>contains, references, missing refs, invalid values</p>
              </DashboardCard>
              <DashboardCard title="Filtered issues" value={String(visibleIssues.length)}>
                <p>{severityFilter === "all" ? "all severities" : severityFilter}</p>
              </DashboardCard>
            </div>
            <h3>Edges</h3>
            {visibleEdges.length ? (
              <ul className="compact-list">
                {visibleEdges.slice(0, 80).map((edge, index) => (
                  <li key={`${edge.source}-${edge.target}-${index}`}>
                    <code>{edge.source}</code> {"->"} <code>{edge.target}</code> 路 {edge.type}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">No edges for the selected issue filter.</p>
            )}
          </div>
        </div>
      ) : (
        <EmptyState title="No validation graph yet." detail="Build the graph after running or editing validation data." />
      )}
      <ErrorPanel message={error} />
    </section>
  );
}

function SocialGraphEditorPanel({
  worldId,
  onPreviewYaml
}: {
  worldId: string;
  onPreviewYaml: (yamlContents: Record<string, string>, validation: AuthoringValidation) => void;
}) {
  const [graph, setGraph] = useState<SocialAuthoringGraph | null>(null);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string>("");
  const [selectedFactionId, setSelectedFactionId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadSocialGraph();
  }, [worldId]);

  const selectedRelationship =
    graph?.relationship_graph.relationships.find((relationship) => relationship.id === selectedRelationshipId)
    ?? graph?.relationship_graph.relationships[0]
    ?? null;
  const selectedFaction =
    graph?.faction_graph.factions.find((faction) => faction.id === selectedFactionId)
    ?? graph?.faction_graph.factions[0]
    ?? null;

  async function loadSocialGraph() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetchSocialAuthoringGraph(worldId);
      setGraph(response);
      setSelectedRelationshipId(response.relationship_graph.relationships[0]?.id ?? "");
      setSelectedFactionId(response.faction_graph.factions[0]?.id ?? "");
      setValidation(null);
    } catch (err) {
      setGraph(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  function updateRelationship(id: string, updater: (relationship: typeof selectedRelationship) => typeof selectedRelationship) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      relationship_graph: {
        ...graph.relationship_graph,
        relationships: graph.relationship_graph.relationships.map((relationship) =>
          relationship.id === id ? updater(relationship) ?? relationship : relationship
        )
      }
    });
  }

  function updateFaction(id: string, updater: (faction: typeof selectedFaction) => typeof selectedFaction) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      faction_graph: {
        ...graph.faction_graph,
        factions: graph.faction_graph.factions.map((faction) =>
          faction.id === id ? updater(faction) ?? faction : faction
        )
      }
    });
  }

  function updateFactionEdge(index: number, field: "source_faction_id" | "target_faction_id" | "visibility" | "relation_type", value: string): void;
  function updateFactionEdge(index: number, field: "relation" | "conflict_level", value: number): void;
  function updateFactionEdge(index: number, field: string, value: string | number) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      faction_graph: {
        ...graph.faction_graph,
        conflict_edges: graph.faction_graph.conflict_edges.map((edge, edgeIndex) =>
          edgeIndex === index ? { ...edge, [field]: value } : edge
        )
      }
    });
  }

  function updateFactionEdgeTags(index: number, tags: string[]) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      faction_graph: {
        ...graph.faction_graph,
        conflict_edges: graph.faction_graph.conflict_edges.map((edge, edgeIndex) =>
          edgeIndex === index ? { ...edge, conflict_tags: tags } : edge
        )
      }
    });
  }

  function addRelationship() {
    if (!graph) {
      return;
    }
    const source = graph.relationship_graph.nodes[0]?.id ?? "player";
    const target = graph.relationship_graph.nodes.find((node) => node.id !== source)?.id ?? "player";
    const id = `relationship_${Date.now()}`;
    setGraph({
      ...graph,
      relationship_graph: {
        ...graph.relationship_graph,
        relationships: [
          ...graph.relationship_graph.relationships,
          {
            id,
            source_id: source,
            target_id: target,
            relation_type: "general",
            trust: 0,
            fear: 0,
            affinity: 0,
            obligation: 0,
            tags: [],
            known_by_player: false,
            hidden_relationship: true,
            hidden_authoring_note: null,
            tone_preset: "derived",
            rp_tone_preview: {
              preset_id: "derived",
              summary: "",
              address_style: "neutral",
              formality: "medium",
              warmth: 0,
              tension: 0,
              intimacy: 0,
              respect: 50,
              resentment: 0,
              fear: 0,
              avoidance: 0,
              trust_expression: "reserved"
            }
          }
        ]
      }
    });
    setSelectedRelationshipId(id);
  }

  function deleteRelationship() {
    if (!graph || !selectedRelationship) {
      return;
    }
    if (!confirmDangerousAction(`Delete relationship "${selectedRelationship.id}" from this authoring draft?`)) {
      return;
    }
    setGraph({
      ...graph,
      relationship_graph: {
        ...graph.relationship_graph,
        relationships: graph.relationship_graph.relationships.filter((relationship) => relationship.id !== selectedRelationship.id)
      }
    });
  }

  function addFactionEdge() {
    if (!graph || graph.faction_graph.factions.length < 2) {
      return;
    }
    setGraph({
      ...graph,
      faction_graph: {
        ...graph.faction_graph,
        conflict_edges: [
          ...graph.faction_graph.conflict_edges,
          {
            source_faction_id: graph.faction_graph.factions[0].id,
            target_faction_id: graph.faction_graph.factions[1].id,
            relation_type: "neutral",
            relation: 0,
            conflict_level: 0,
            visibility: "hidden",
            conflict_tags: []
          }
        ]
      }
    });
  }

  function deleteFactionEdge(index: number) {
    if (!graph) {
      return;
    }
    setGraph({
      ...graph,
      faction_graph: {
        ...graph.faction_graph,
        conflict_edges: graph.faction_graph.conflict_edges.filter((_, edgeIndex) => edgeIndex !== index)
      }
    });
  }

  async function previewSocialGraph() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewSocialAuthoringGraph(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Social graph preview is valid." : "Social graph preview has errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function validateSocialGraph() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await validateSocialAuthoringGraph(worldId, graph);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.validation.ok ? "Social graph validation passed." : "Social graph validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function saveSocialGraph() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const validationResponse = await validateSocialAuthoringGraph(worldId, graph);
      setValidation(validationResponse.validation);
      onPreviewYaml(validationResponse.yaml_contents, validationResponse.validation);
      if (!validationResponse.validation.ok) {
        setMessage("Social graph has validation errors. Fix them before saving.");
        return;
      }
      if (validationResponse.validation.warnings.length > 0 && !confirmDangerousAction("Social graph has warnings. Save anyway?")) {
        setMessage("Save cancelled.");
        return;
      }
      if (!confirmDangerousAction(DANGEROUS_ACTION_COPY.saveGraphChanges)) {
        setMessage("Save cancelled.");
        return;
      }
      const response = await saveSocialAuthoringGraph(worldId, graph, validationResponse.validation.warnings.length > 0);
      setGraph(response.graph);
      setValidation(response.validation);
      onPreviewYaml(response.yaml_contents, response.validation);
      setMessage(response.saved ? "Social graph saved." : "Social graph was not saved.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="quest-graph-editor">
      <div className="authoring-pane-header">
        <div>
          <h2>Faction / Relationship Editor</h2>
          <p className="muted">Authoring-only social graph editor. Player graph filtering remains separate.</p>
        </div>
        <button type="button" onClick={() => void loadSocialGraph()} disabled={isBusy}>
          Reload Social Graph
        </button>
      </div>

      {graph ? (
        <div className="quest-graph-grid">
          <aside className="quest-graph-list">
            <h3>Relationships</h3>
            {graph.relationship_graph.relationships.map((relationship) => (
              <button
                type="button"
                key={relationship.id}
                className={relationship.id === selectedRelationship?.id ? "selected" : ""}
                onClick={() => setSelectedRelationshipId(relationship.id)}
              >
                <span>{relationship.source_id} {"->"} {relationship.target_id}</span>
                <span className="file-category">{relationship.relation_type}</span>
              </button>
            ))}
            <button type="button" onClick={addRelationship} disabled={isBusy}>
              Add Relationship
            </button>
            <h3>Factions</h3>
            {graph.faction_graph.factions.map((faction) => (
              <button
                type="button"
                key={faction.id}
                className={faction.id === selectedFaction?.id ? "selected" : ""}
                onClick={() => setSelectedFactionId(faction.id)}
              >
                <span>{faction.name}</span>
                <span className="file-category">{faction.known_by_player ? "known" : "hidden"}</span>
              </button>
            ))}
          </aside>

          <section className="quest-graph-detail">
            {selectedRelationship && (
              <section className="studio-section">
                <h3>NPC Relationship Edge</h3>
                <div className="form-grid">
                  <label>
                    Source
                    <select
                      value={selectedRelationship.source_id}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, source_id: event.target.value } : item)}
                      disabled={isBusy}
                    >
                      {graph.relationship_graph.nodes.map((node) => (
                        <option key={node.id} value={node.id}>{node.label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Target
                    <select
                      value={selectedRelationship.target_id}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, target_id: event.target.value } : item)}
                      disabled={isBusy}
                    >
                      {graph.relationship_graph.nodes.map((node) => (
                        <option key={node.id} value={node.id}>{node.label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Relation type
                    <input
                      value={selectedRelationship.relation_type}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, relation_type: event.target.value } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  {(["trust", "fear", "affinity", "obligation"] as const).map((field) => (
                    <label key={field}>
                      {field}
                      <input
                        type="number"
                        value={selectedRelationship[field]}
                        onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, [field]: Number(event.target.value) } : item)}
                        disabled={isBusy}
                      />
                    </label>
                  ))}
                  <label>
                    Hidden relationship
                    <input
                      type="checkbox"
                      checked={selectedRelationship.hidden_relationship}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, hidden_relationship: event.target.checked, known_by_player: event.target.checked ? false : item.known_by_player } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Player known
                    <input
                      type="checkbox"
                      checked={selectedRelationship.known_by_player}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, known_by_player: event.target.checked } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    RP tone preset
                    <select
                      value={selectedRelationship.tone_preset ?? "derived"}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, tone_preset: event.target.value } : item)}
                      disabled={isBusy}
                    >
                      {graph.relationship_graph.relationship_tone_presets.map((preset) => (
                        <option key={preset.id} value={preset.id}>{preset.label}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Tags
                    <input
                      value={selectedRelationship.tags.join(", ")}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, tags: splitCsv(event.target.value) } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label className="full-width">
                    Hidden authoring note
                    <input
                      value={selectedRelationship.hidden_authoring_note ?? ""}
                      onChange={(event) => updateRelationship(selectedRelationship.id, (item) => item ? { ...item, hidden_authoring_note: event.target.value || null } : item)}
                      disabled={isBusy}
                    />
                  </label>
                </div>
                <div className="authoring-preview-box">
                  <strong>RP tone preview</strong>
                  <p className="muted">{selectedRelationship.rp_tone_preview.summary || "Preview updates after preview/validate."}</p>
                  <p className="muted">
                    warmth {selectedRelationship.rp_tone_preview.warmth} / tension {selectedRelationship.rp_tone_preview.tension} / intimacy {selectedRelationship.rp_tone_preview.intimacy}
                  </p>
                </div>
                <button type="button" onClick={deleteRelationship} disabled={isBusy}>
                  Delete Relationship
                </button>
              </section>
            )}

            {selectedFaction && (
              <section className="studio-section">
                <h3>Faction Node</h3>
                <div className="form-grid">
                  <label>
                    Name
                    <input
                      value={selectedFaction.name}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, name: event.target.value } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Known by player
                    <input
                      type="checkbox"
                      checked={selectedFaction.known_by_player}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, known_by_player: event.target.checked } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Default reputation
                    <input
                      type="number"
                      value={selectedFaction.default_reputation}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, default_reputation: Number(event.target.value) } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Alert level
                    <input
                      type="number"
                      value={selectedFaction.default_alert_level}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, default_alert_level: Number(event.target.value) } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Conflict level
                    <input
                      type="number"
                      value={selectedFaction.default_conflict_level}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, default_conflict_level: Number(event.target.value) } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label>
                    Visibility
                    <select
                      value={selectedFaction.visibility}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, visibility: event.target.value, known_by_player: event.target.value === "player_visible" } : item)}
                      disabled={isBusy}
                    >
                      <option value="player_visible">player_visible</option>
                      <option value="hidden">hidden</option>
                    </select>
                  </label>
                  <label>
                    Conflict tags
                    <input
                      value={selectedFaction.conflict_tags.join(", ")}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, conflict_tags: splitCsv(event.target.value) } : item)}
                      disabled={isBusy}
                    />
                  </label>
                  <label className="full-width">
                    Description
                    <textarea
                      value={selectedFaction.description}
                      onChange={(event) => updateFaction(selectedFaction.id, (item) => item ? { ...item, description: event.target.value } : item)}
                      disabled={isBusy}
                    />
                  </label>
                </div>
              </section>
            )}

            <section className="studio-section">
              <h3>Faction Conflict Edges</h3>
              {graph.faction_graph.conflict_edges.map((edge, index) => (
                <div className="authoring-preview-box" key={`${edge.source_faction_id}-${edge.target_faction_id}-${index}`}>
                  <div className="form-grid">
                    <label>
                      Source faction
                      <select value={edge.source_faction_id} onChange={(event) => updateFactionEdge(index, "source_faction_id", event.target.value)} disabled={isBusy}>
                        {graph.faction_graph.factions.map((faction) => <option key={faction.id} value={faction.id}>{faction.id}</option>)}
                      </select>
                    </label>
                    <label>
                      Target faction
                      <select value={edge.target_faction_id} onChange={(event) => updateFactionEdge(index, "target_faction_id", event.target.value)} disabled={isBusy}>
                        {graph.faction_graph.factions.map((faction) => <option key={faction.id} value={faction.id}>{faction.id}</option>)}
                      </select>
                    </label>
                    <label>
                      Relation
                      <input type="number" value={edge.relation} onChange={(event) => updateFactionEdge(index, "relation", Number(event.target.value))} disabled={isBusy} />
                    </label>
                  <label>
                    Conflict level
                    <input type="number" value={edge.conflict_level} onChange={(event) => updateFactionEdge(index, "conflict_level", Number(event.target.value))} disabled={isBusy} />
                  </label>
                  <label>
                    Relation type
                    <select value={edge.relation_type} onChange={(event) => updateFactionEdge(index, "relation_type", event.target.value)} disabled={isBusy}>
                      <option value="alliance">alliance</option>
                      <option value="hostility">hostility</option>
                      <option value="conflict">conflict</option>
                      <option value="neutral">neutral</option>
                    </select>
                  </label>
                  <label>
                    Visibility
                    <select value={edge.visibility} onChange={(event) => updateFactionEdge(index, "visibility", event.target.value)} disabled={isBusy}>
                        <option value="hidden">hidden</option>
                        <option value="player_visible">player_visible</option>
                      </select>
                    </label>
                    <label>
                      Conflict tags
                      <input value={edge.conflict_tags.join(", ")} onChange={(event) => updateFactionEdgeTags(index, splitCsv(event.target.value))} disabled={isBusy} />
                    </label>
                  </div>
                  <button type="button" onClick={() => deleteFactionEdge(index)} disabled={isBusy}>Delete Edge</button>
                </div>
              ))}
              <button type="button" onClick={addFactionEdge} disabled={isBusy || graph.faction_graph.factions.length < 2}>
                Add Faction Edge
              </button>
            </section>

            <AuthoringActionBar
              onPreview={() => void previewSocialGraph()}
              onValidate={() => void validateSocialGraph()}
              onSave={() => void saveSocialGraph()}
              disabled={!graph || isBusy}
              previewLabel="Preview YAML"
              saveLabel="Save Social Graph"
            />
            <PreviewResultPanel title="Faction / Relationship Validation" validation={validation} />
          </section>
        </div>
      ) : (
        <EmptyState title="No social graph loaded." detail="Load factions.yaml or relationships.yaml through authoring." />
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
}

function ModManagerPanel() {
  const [mods, setMods] = useState<AuthoringModSummary[]>([]);
  const [selectedModId, setSelectedModId] = useState<string>("");
  const [validationByModId, setValidationByModId] = useState<Record<string, AuthoringModValidation>>({});
  const [loadOrder, setLoadOrder] = useState<AuthoringModLoadOrderResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadMods();
  }, []);

  async function loadMods() {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const [modsResponse, loadOrderResponse] = await Promise.all([
        fetchAuthoringMods(),
        fetchAuthoringModLoadOrder()
      ]);
      setMods(modsResponse.mods);
      setSelectedModId((current) => current || modsResponse.mods[0]?.id || "");
      setLoadOrder(loadOrderResponse);
    } catch (err) {
      setMods([]);
      setLoadOrder(null);
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidate(modId: string) {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const [detail, validation] = await Promise.all([
        fetchAuthoringMod(modId),
        validateAuthoringMod(modId)
      ]);
      setValidationByModId((previous) => ({
        ...previous,
        [modId]: detail.validation ?? validation
      }));
      setMessage(validation.ok ? "Mod validation passed." : "Mod validation found errors.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  async function handleExportMod(modId: string) {
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const exported = await exportModArchive(modId);
      setMessage(
        `Mod archive ready: ${exported.file_name}. Imports remain local-only and run mod validation before install.`
      );
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const selectedMod = mods.find((mod) => mod.id === selectedModId) ?? null;
  const selectedValidation = selectedModId ? validationByModId[selectedModId] : undefined;

  return (
    <section className="mod-manager-panel authoring-zone">
      <header className="authoring-pane-header">
        <div>
          <h2>Mod Manager</h2>
          <p className="muted">Local content-only mods. No scripts are executed.</p>
        </div>
        <button type="button" onClick={() => void loadMods()} disabled={isBusy}>
          Refresh Mods
        </button>
      </header>

      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice api-disabled-notice">
          Mod Manager uses the local authoring API. Set <code>ENABLE_AUTHORING_API=true</code>.
        </div>
      )}
      <LocalOnlyNotice>
        Mods are YAML/content only in this studio. The manager validates dependencies, conflicts,
        and load order without executing mod code.
      </LocalOnlyNotice>
      <ErrorPanel message={error} />
      {message && <p className="muted">{message}</p>}

      <div className="mod-manager-grid">
        <aside className="mod-list">
          {mods.length === 0 && <EmptyState title="No local mods discovered." detail="Place content-only mods in the configured mods root." />}
          {mods.map((mod) => (
            <button
              type="button"
              key={mod.id}
              className={`save-card ${selectedModId === mod.id ? "selected" : ""}`}
              onClick={() => setSelectedModId(mod.id)}
            >
              <strong>{mod.name}</strong>
              <span>{mod.id}</span>
              <span>v{mod.version}</span>
              <span className="muted">
                {validationByModId[mod.id]?.ok === false
                  ? "validation errors"
                  : validationByModId[mod.id]?.ok
                    ? "valid"
                    : "not validated"}
              </span>
            </button>
          ))}
        </aside>

        <section className="mod-detail">
          {selectedMod ? (
            <>
              <div className="mod-detail-header">
                <div>
                  <h3>{selectedMod.name}</h3>
                  <p className="muted">{selectedMod.description || "No description."}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void handleValidate(selectedMod.id)}
                  disabled={isBusy}
                >
                  Validate Mod
                </button>
                <button
                  type="button"
                  onClick={() => void handleExportMod(selectedMod.id)}
                  disabled={isBusy}
                >
                  Export Mod
                </button>
              </div>

              <dl className="metadata-list">
                <dt>Id</dt>
                <dd>{selectedMod.id}</dd>
                <dt>Version</dt>
                <dd>{selectedMod.version}</dd>
                <dt>Enabled</dt>
                <dd>Read-only in v0.7.3</dd>
                <dt>Engine</dt>
                <dd>
                  {selectedMod.engine_version_min}
                  {selectedMod.engine_version_max ? ` - ${selectedMod.engine_version_max}` : " or newer"}
                </dd>
                <dt>Content schema</dt>
                <dd>{selectedMod.content_schema_version}</dd>
                <dt>Worlds</dt>
                <dd>{selectedMod.compatible_worlds.join(", ") || "Not specified"}</dd>
                <dt>Load hint</dt>
                <dd>{selectedMod.load_order_hint}</dd>
              </dl>

              <div className="mod-info-columns">
                <ModListBlock title="Dependencies" values={selectedMod.dependencies} />
                <ModListBlock title="Optional" values={selectedMod.optional_dependencies} />
                <ModListBlock title="Conflicts" values={selectedMod.conflicts} />
                <ModListBlock title="Entry Worlds" values={selectedMod.entry_worlds} />
              </div>

              <section className="studio-section">
                <h3>Dependency Graph</h3>
                <p className="muted">
                  {selectedMod.dependencies.length
                    ? `${selectedMod.id} depends on ${selectedMod.dependencies.join(", ")}`
                    : `${selectedMod.id} has no required dependencies.`}
                </p>
              </section>

              <section className="studio-section">
                <h3>Load Order</h3>
                {loadOrder?.ok ? (
                  <p className="muted">{loadOrder.load_order.join(" -> ") || "No enabled mods."}</p>
                ) : (
                  <ItemList emptyText="No load-order errors." items={(loadOrder?.errors ?? []).map((item) => <span key={item}>{item}</span>)} />
                )}
              </section>

              <section className="studio-section">
                <h3>Migration Notes</h3>
                <p className="muted">{selectedMod.migration_notes || "No migration notes."}</p>
              </section>

              <section className="studio-section">
                <h3>Validation</h3>
                {selectedValidation ? (
                  <>
                    <StatusBadge label={selectedValidation.ok ? "Valid" : "Errors found"} enabled={selectedValidation.ok} />
                    <ValidationIssueList issues={selectedValidation.errors} onSelectIssue={() => undefined} />
                    {selectedValidation.warnings.length > 0 && (
                      <ValidationIssueList issues={selectedValidation.warnings} onSelectIssue={() => undefined} />
                    )}
                  </>
                ) : (
                  <EmptyState title="Not validated." detail="Run validation to inspect manifest, dependencies, conflicts, and content." />
                )}
              </section>
            </>
          ) : (
            <EmptyState title="No mod selected." detail="Select a discovered local mod to inspect." />
          )}
        </section>
      </div>
    </section>
  );
}

function ModListBlock({ title, values }: { title: string; values: string[] }) {
  return (
    <section className="studio-section">
      <h3>{title}</h3>
      <p className="muted">{values.join(", ") || "None"}</p>
    </section>
  );
}

function ValidationPanel({
  validation,
  preview,
  onSelectIssue
}: {
  validation: AuthoringValidation | null;
  preview?: AuthoringFilePreviewResponse | null;
  onSelectIssue: (issue: AuthoringValidation["errors"][number]) => void;
}) {
  if (!validation) {
    return <EmptyState title="No validation result yet." detail="Run Validate or Preview to populate this panel." />;
  }
  const groupedIssues = groupValidationIssues(validation);
  return (
    <section className="validation-panel">
      <h2>Validation</h2>
      <p className={validation.ok ? "validation-ok" : "error"}>
        {validation.ok ? "Loadable" : "Errors must be fixed before loading."}
      </p>
      {preview && (
        <section className="diff-summary">
          <h3>Dry Run / Diff</h3>
          <dl>
            <dt>Parsed</dt>
            <dd>{preview.parsed_ok ? "ok" : "failed"}</dd>
            <dt>Lines</dt>
            <dd>
              {preview.diff_summary.line_count_before} {"->"} {preview.diff_summary.line_count_after}
            </dd>
            <dt>Added</dt>
            <dd>{preview.diff_summary.added_ids.join(", ") || "None"}</dd>
            <dt>Removed</dt>
            <dd>{preview.diff_summary.removed_ids.join(", ") || "None"}</dd>
            <dt>Changed</dt>
            <dd>{preview.diff_summary.changed_ids.join(", ") || "None"}</dd>
            <dt>Save impact</dt>
            <dd>{preview.potential_save_migration_required ? "review required" : "none detected"}</dd>
          </dl>
        </section>
      )}
      {Object.entries(groupedIssues).map(([file, issues]) => (
        <div className="validation-file-group" key={file}>
          <h3>{file}</h3>
          <ValidationIssueList issues={issues} onSelectIssue={onSelectIssue} />
        </div>
      ))}
      {Object.keys(groupedIssues).length === 0 && <EmptyState title="No issues." />}
    </section>
  );
}

function WorldFileTree({
  files,
  selectedFile,
  validation,
  onSelectFile
}: {
  files: string[];
  selectedFile: string;
  validation: AuthoringValidation | null;
  onSelectFile: (fileName: string) => void;
}) {
  const validationCounts = useMemo(() => fileIssueCounts(validation), [validation]);
  return (
    <aside className="authoring-file-tree">
      <h2>World Files</h2>
      {AUTHORING_FILE_GROUPS.map((group) => {
        const groupFiles = group.files.filter((fileName, index) => {
          return files.includes(fileName) && group.files.indexOf(fileName) === index;
        });
        if (groupFiles.length === 0) {
          return null;
        }
        return (
          <section key={group.title}>
            <h3>{group.title}</h3>
            <div className="file-button-list">
              {groupFiles.map((fileName) => {
                const counts = validationCounts[fileName] ?? { errors: 0, warnings: 0 };
                return (
                  <button
                    type="button"
                    key={`${group.title}-${fileName}`}
                    className={`file-button ${selectedFile === fileName ? "selected" : ""}`}
                    onClick={() => onSelectFile(fileName)}
                  >
                    <span>{fileName}</span>
                    <span className="file-category">{fileCategoryLabel(fileName)}</span>
                    {(counts.errors > 0 || counts.warnings > 0) && (
                      <span className="file-issues">
                        {counts.errors > 0 ? `${counts.errors} errors` : ""}
                        {counts.errors > 0 && counts.warnings > 0 ? " / " : ""}
                        {counts.warnings > 0 ? `${counts.warnings} warnings` : ""}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </section>
        );
      })}
    </aside>
  );
}

function AuthoringFormEditor({
  fileName,
  entities,
  selectedEntity,
  selectedEntityId,
  disabled,
  onSelectEntity,
  onChangeField
}: {
  fileName: string;
  entities: ParsedAuthoringEntity[];
  selectedEntity: ParsedAuthoringEntity | null;
  selectedEntityId: string;
  disabled: boolean;
  onSelectEntity: (entityId: string) => void;
  onChangeField: (fieldName: string, value: string) => void;
}) {
  const fields = FORM_FIELDS[fileName] ?? [];
  if (entities.length === 0 || !selectedEntity) {
    return (
      <div className="form-editor-empty">
        <p className="muted">
          No editable entities were detected for this file. Use Raw YAML for complex changes.
        </p>
      </div>
    );
  }

  return (
    <div className="form-editor">
      <label>
        Entity
        <select
          value={selectedEntityId || selectedEntity.id}
          onChange={(event) => onSelectEntity(event.target.value)}
          disabled={disabled}
        >
          {entities.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.id}
            </option>
          ))}
        </select>
      </label>
      <div className="form-grid">
        {fields.map((field) => {
          const value = selectedEntity.fields[field.name] ?? "";
          if (field.kind === "textarea") {
            return (
              <label key={field.name} className="wide-field">
                {field.label}
                <textarea
                  value={value}
                  onChange={(event) => onChangeField(field.name, event.target.value)}
                  disabled={disabled}
                />
              </label>
            );
          }
          if (field.kind === "boolean") {
            return (
              <label key={field.name} className="checkbox-field">
                <input
                  type="checkbox"
                  checked={value === "true"}
                  onChange={(event) => onChangeField(field.name, event.target.checked ? "true" : "false")}
                  disabled={disabled}
                />
                {field.label}
              </label>
            );
          }
          if (field.kind === "select") {
            return (
              <label key={field.name}>
                {field.label}
                <select
                  value={value}
                  onChange={(event) => onChangeField(field.name, event.target.value)}
                  disabled={disabled}
                >
                  <option value="">Unset</option>
                  {(field.options ?? []).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
            );
          }
          return (
            <label key={field.name}>
              {field.label}
              <input
                type={field.kind === "number" ? "number" : "text"}
                value={value}
                onChange={(event) => onChangeField(field.name, event.target.value)}
                disabled={disabled}
              />
            </label>
          );
        })}
      </div>
      <p className="muted">
        Form edits update simple top-level fields only. Use Raw YAML for nested schedules, stages,
        triggers, goals, and relationship details.
      </p>
    </div>
  );
}

function AuthoringPreviewPanel({
  fileName,
  content,
  validation,
  preview,
  entities,
  selectedEntity
}: {
  fileName: string;
  content: string;
  validation: AuthoringValidation | null;
  preview?: AuthoringFilePreviewResponse | null;
  entities: ParsedAuthoringEntity[];
  selectedEntity: ParsedAuthoringEntity | null;
}) {
  const issues = validation
    ? [...validation.errors, ...validation.warnings, ...validation.suggestions].filter(
        (issue) => issue.file === fileName
      )
    : [];
  return (
    <aside className="authoring-preview">
      <h2>Preview</h2>
      <dl>
        <dt>File</dt>
        <dd>{fileName}</dd>
        <dt>Entities</dt>
        <dd>{entities.length}</dd>
        <dt>Validation issues</dt>
        <dd>{issues.length}</dd>
        <dt>Size</dt>
        <dd>{content.length} chars</dd>
      </dl>
      {selectedEntity ? (
        <div>
          <h3>{selectedEntity.id}</h3>
          <AuthoringPreviewCode content={JSON.stringify(selectedEntity.fields, null, 2)} />
        </div>
      ) : (
        <p className="muted">Select an entity or use Raw YAML for manifest-level files.</p>
      )}
      {preview && (
        <div>
          <h3>Impact Analysis</h3>
          <ItemList
            emptyText="No potentially affected objects."
            items={[
              ...preview.impact.removed_locations.map((id) => <span key={`loc-${id}`}>removed location: {id}</span>),
              ...preview.impact.removed_npcs.map((id) => <span key={`npc-${id}`}>removed NPC: {id}</span>),
              ...preview.impact.removed_items.map((id) => <span key={`item-${id}`}>removed item: {id}</span>),
              ...preview.impact.removed_facts.map((id) => <span key={`fact-${id}`}>removed fact: {id}</span>),
              ...preview.impact.removed_quests.map((id) => <span key={`quest-${id}`}>removed quest: {id}</span>),
              ...preview.impact.removed_factions.map((id) => <span key={`faction-${id}`}>removed faction: {id}</span>),
              ...preview.impact.changed_location_exits.map((id) => <span key={`exit-${id}`}>changed exits: {id}</span>),
              ...preview.impact.renamed_ids.map((id) => <span key={`rename-${id}`}>possible rename: {id}</span>)
            ]}
          />
          {preview.impact.notes.length > 0 && (
            <ul className="compact-list">
              {preview.impact.notes.map((note) => (
                <li key={note}>{redactReportText(note)}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </aside>
  );
}

function ValidationIssueList({
  issues,
  onSelectIssue
}: {
  issues: AuthoringValidation["errors"];
  onSelectIssue: (issue: AuthoringValidation["errors"][number]) => void;
}) {
  return (
    <div>
      {issues.length === 0 ? (
        <p className="muted">None</p>
      ) : (
        <ul className="compact-list">
          {issues.map((issue, index) => (
            <li key={`${issue.path}-${index}`}>
              <button
                className="issue-button"
                type="button"
                onClick={() => onSelectIssue(issue)}
              >
                <span className={`severity ${issue.severity}`}>{issue.severity}</span>
                <strong>{redactReportText(issue.path)}</strong>
                <span>{redactReportText(issue.code)}</span>
                <span>{redactReportText(issue.message)}</span>
                {issue.ref_id && <span>ref: {redactReportText(issue.ref_id)}</span>}
                {issue.suggestion && <span>fix: {redactReportText(issue.suggestion)}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ItemList({ items, emptyText }: { items: ReactNode[]; emptyText: string }) {
  if (items.length === 0) {
    return <p className="muted">{emptyText}</p>;
  }
  return <ul className="compact-list">{items.map((item, index) => <li key={index}>{item}</li>)}</ul>;
}

function DebugEventSummary({ events, emptyText }: { events: DebugEvent[]; emptyText: string }) {
  if (events.length === 0) {
    return <p className="muted">{emptyText}</p>;
  }
  return (
    <div className="debug-event-list">
      {events.map((event) => (
        <details className="timeline-event" key={event.event_id}>
          <summary>
            <span>Turn {event.turn}</span>
            <span>{event.action_type}</span>
            <span>{event.actor_id}</span>
            <span>{event.result}</span>
          </summary>
          <pre>{JSON.stringify(event.state_deltas, null, 2)}</pre>
        </details>
      ))}
    </div>
  );
}

function EventLogViewerPanel({
  events,
  error,
  selectedSaveId,
  hasSession,
  onLoadSession,
  onLoadSave,
  debugEnabled
}: {
  events: DebugEvent[];
  error: string;
  selectedSaveId: string;
  hasSession: boolean;
  onLoadSession: () => void;
  onLoadSave: () => void;
  debugEnabled: boolean;
}) {
  const [turnFilter, setTurnFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [moduleFilter, setModuleFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const eventTypes = useMemo(() => sortedUnique(events.map((event) => eventLogSafeType(event))), [events]);
  const actors = useMemo(() => sortedUnique(events.map((event) => eventLogSafeActor(event))), [events]);
  const sourceModules = useMemo(() => sortedUnique(events.map((event) => eventLogSafeSourceModule(event))), [events]);
  const tags = useMemo(() => sortedUnique(events.flatMap((event) => eventLogSafeTags(event))), [events]);
  const filteredEvents = useMemo(
    () =>
      events.filter((event) => {
        if (turnFilter && event.turn !== Number(turnFilter)) return false;
        if (eventTypeFilter && eventLogSafeType(event) !== eventTypeFilter) return false;
        if (actorFilter && eventLogSafeActor(event) !== actorFilter) return false;
        if (moduleFilter && eventLogSafeSourceModule(event) !== moduleFilter) return false;
        if (tagFilter && !eventLogSafeTags(event).includes(tagFilter)) return false;
        return true;
      }),
    [actorFilter, eventTypeFilter, events, moduleFilter, tagFilter, turnFilter]
  );

  return (
    <section className="debug-group timeline eventlog-viewer">
      <div className="authoring-pane-header">
        <div>
          <h2>EventLog Viewer Pro</h2>
          <p className="muted">
            Read-only EventLog inspection. Normal rows show safe summaries and linked StateDelta counts; raw details require DebugGate.
          </p>
        </div>
        <StatusBadge label={debugEnabled ? "Debug details gated on" : "Debug details disabled"} enabled={debugEnabled} />
      </div>
      <div className="timeline-controls">
        <button type="button" onClick={onLoadSession} disabled={!hasSession}>
          Load Session EventLog
        </button>
        <button type="button" onClick={onLoadSave} disabled={!selectedSaveId}>
          Load Save EventLog
        </button>
        <label>
          Turn
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="any"
            value={turnFilter}
            onChange={(event) => setTurnFilter(event.target.value.replace(/\D/g, ""))}
          />
        </label>
        <label>
          Event type
          <select value={eventTypeFilter} onChange={(event) => setEventTypeFilter(event.target.value)}>
            <option value="">All types</option>
            {eventTypes.map((eventType) => (
              <option key={eventType} value={eventType}>
                {eventType}
              </option>
            ))}
          </select>
        </label>
        <label>
          Actor
          <select value={actorFilter} onChange={(event) => setActorFilter(event.target.value)}>
            <option value="">All actors</option>
            {actors.map((actor) => (
              <option key={actor} value={actor}>
                {actor}
              </option>
            ))}
          </select>
        </label>
        <label>
          Source module
          <select value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)}>
            <option value="">All modules</option>
            {sourceModules.map((source) => (
              <option key={source} value={source}>
                {source}
              </option>
            ))}
          </select>
        </label>
        <label>
          Tags
          <select value={tagFilter} onChange={(event) => setTagFilter(event.target.value)}>
            <option value="">All tags</option>
            {tags.map((tag) => (
              <option key={tag} value={tag}>
                {tag}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && <p className="error">{redactReportText(error)}</p>}
      {error && error.toLowerCase().includes("debug") && <p className="muted">ENABLE_DEBUG_API required for loading raw debug-backed EventLog data.</p>}
      {!error && events.length === 0 && (
        <EmptyState title="No EventLog events loaded." detail="Load a session or save EventLog. This viewer is read-only and cannot modify EventLog or GameState." />
      )}
      {events.length > 0 && filteredEvents.length === 0 && (
        <EmptyState title="No events match these filters." detail="Try another turn, event type, actor, source module, or tag." />
      )}
      {filteredEvents.length > 0 && (
        <div className="debug-event-list">
          {filteredEvents.map((event) => (
            <EventLogSafeCard event={event} debugEnabled={debugEnabled} key={event.event_id} />
          ))}
        </div>
      )}
    </section>
  );
}

const HIDDEN_LEAK_CATEGORIES = [
  "visible_state leak",
  "prompt leak",
  "Tavern leak",
  "Novel leak",
  "World UI leak",
  "export leak",
  "diagnostics leak",
  "backup leak",
  "debug leak"
] as const;

type HiddenLeakCategory = (typeof HIDDEN_LEAK_CATEGORIES)[number];
type HiddenLeakIssue = {
  id: string;
  category: HiddenLeakCategory;
  severity: "blocker" | "warning" | "info";
  source: string;
  target: string;
  safeSummary: string;
  suggestedAction: string;
};

function HiddenLeakReportPanel({
  visibleState,
  events,
  worldHealth,
  narrativeEvalReports,
  diagnosticsBundlePreview,
  backupPlan,
  selectedWorldId,
  onRunLeakCheck
}: {
  visibleState: VisibleState | null;
  events: DebugEvent[];
  worldHealth: WorldHealthScore | null;
  narrativeEvalReports: NarrativeEvalReport[];
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null;
  backupPlan: BackupPlan | null;
  selectedWorldId: string;
  onRunLeakCheck: () => void;
}) {
  const [category, setCategory] = useState<HiddenLeakCategory | "all">("all");
  const issues = useMemo(
    () => buildHiddenLeakIssues(visibleState, events, worldHealth, narrativeEvalReports, diagnosticsBundlePreview, backupPlan),
    [backupPlan, diagnosticsBundlePreview, events, narrativeEvalReports, visibleState, worldHealth]
  );
  const filteredIssues = category === "all" ? issues : issues.filter((issue) => issue.category === category);
  const blockerCount = issues.filter((issue) => issue.severity === "blocker").length;
  const warningCount = issues.filter((issue) => issue.severity === "warning").length;
  const status = blockerCount ? "blocked" : warningCount ? "review" : issues.length ? "clear with notes" : "no report";

  return (
    <section className="debug-group hidden-leak-report">
      <div className="authoring-pane-header">
        <div>
          <h2>Hidden Leak Report UI Pro</h2>
          <p className="muted">
            Safe local leak report for visible_state, prompts, mode UIs, exports, diagnostics, backups, and debug surfaces. Hidden text and secrets are never printed.
          </p>
        </div>
        <ValidationStatusBadge status={blockerCount ? "failed" : warningCount ? "warning" : issues.length ? "passed" : "not_run"} />
      </div>
      <FilterToolbar>
        <button type="button" onClick={onRunLeakCheck} disabled={!selectedWorldId}>
          Run Leak Check
        </button>
        <label>
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value as HiddenLeakCategory | "all")}>
            <option value="all">All categories</option>
            {HIDDEN_LEAK_CATEGORIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </FilterToolbar>
      <div className="timeline-summary">
        <span>overall: {status}</span>
        <span>{blockerCount} blockers</span>
        <span>{warningCount} warnings</span>
        <span>{issues.length} safe issue rows</span>
      </div>
      {issues.length === 0 ? (
        <EmptyState title="No hidden leak report loaded." detail="Run the local leak check or load quality reports. This panel never uploads data or calls an external LLM judge." />
      ) : filteredIssues.length === 0 ? (
        <EmptyState title="No issues in this category." detail="Try another category or run the local leak check again." />
      ) : (
        <div className="debug-event-list">
          {filteredIssues.map((issue) => (
            <div className="section-card" key={issue.id}>
              <div className="card-header">
                <h3>{issue.category}</h3>
                <LeakRiskBadge severity={issue.severity} />
              </div>
              <dl className="event-details">
                <dt>Source</dt>
                <dd>{issue.source}</dd>
                <dt>Target</dt>
                <dd>{issue.target}</dd>
                <dt>Safe summary</dt>
                <dd>{issue.safeSummary}</dd>
                <dt>Suggested action</dt>
                <dd>{issue.suggestedAction}</dd>
              </dl>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

function buildHiddenLeakIssues(
  visibleState: VisibleState | null,
  events: DebugEvent[],
  worldHealth: WorldHealthScore | null,
  narrativeEvalReports: NarrativeEvalReport[],
  diagnosticsBundlePreview: DiagnosticsBundlePreview | null,
  backupPlan: BackupPlan | null
): HiddenLeakIssue[] {
  const issues: HiddenLeakIssue[] = [];
  const visibleMarkers = hiddenLeakMarkers(visibleState);
  visibleMarkers.forEach((marker, index) => {
    issues.push(hiddenLeakIssue("visible_state leak", "blocker", `visible_state:${index}`, "visible_state", "normal UI", marker, "Inspect visibility rules and remove hidden/debug markers from visible_state."));
  });
  const rawDeltaVisibleEvents = events.filter((event) => event.visible_to_player && event.state_deltas.length > 0);
  if (rawDeltaVisibleEvents.length > 0) {
    issues.push(hiddenLeakIssue("debug leak", "warning", "visible-state-delta-count", "EventLog", "debug viewer", `${rawDeltaVisibleEvents.length} visible event(s) have StateDelta records; raw payloads must stay debug-gated.`, "Keep raw StateDelta rendering inside DebugGate and expose only safe counts in normal UI."));
  }
  events.filter((event) => !event.visible_to_player).slice(0, 8).forEach((event) => {
    issues.push(hiddenLeakIssue("debug leak", "info", `debug-event-${event.event_id}`, "EventLog", "normal UI", `Debug-only event ${redactReportText(event.event_id)} is gated from normal report.`, "No action required unless this event appears in normal/player UI."));
  });
  collectLeakStrings(worldHealth?.blockers ?? [], "World Health blocker").forEach((item, index) => {
    issues.push(hiddenLeakIssue("World UI leak", "blocker", `world-health-blocker-${index}`, "Quality Gate", "World UI", item, "Fix the reported visibility/export/debug boundary before release."));
  });
  collectLeakStrings(worldHealth?.warnings ?? [], "World Health warning").forEach((item, index) => {
    issues.push(hiddenLeakIssue("World UI leak", "warning", `world-health-warning-${index}`, "Quality Gate", "World UI", item, "Review the warning and add/adjust a local leak regression if needed."));
  });
  narrativeEvalReports.flatMap((report) => Object.values(report.failure_reasons).flat()).forEach((reason, index) => {
    if (isLeakText(reason)) {
      issues.push(hiddenLeakIssue("Novel leak", "warning", `novel-eval-${index}`, "Narrative Eval", "Novel Studio", reason, "Review Novel prompt/export context and keep hidden facts out of normal prose reports."));
    }
  });
  const diagnosticsMarkers = hiddenLeakMarkers(diagnosticsBundlePreview);
  diagnosticsMarkers.forEach((marker, index) => {
    issues.push(hiddenLeakIssue("diagnostics leak", "warning", `diagnostics-${index}`, "Diagnostics Bundle Preview", "diagnostics", marker, "Keep diagnostics preview/create exclusions and redaction enabled."));
  });
  const backupMarkers = hiddenLeakMarkers(backupPlan);
  backupMarkers.forEach((marker, index) => {
    issues.push(hiddenLeakIssue("backup leak", "warning", `backup-${index}`, "Backup Plan", "backup", marker, "Keep backup exclusions for secrets, debug data, mature/private content, logs, and databases enabled."));
  });
  HIDDEN_LEAK_CATEGORIES.forEach((category) => {
    if (!issues.some((issue) => issue.category === category)) {
      issues.push(hiddenLeakIssue(category, "info", `clear-${category}`, "local report", category, "No leak marker found in currently loaded safe summaries.", "No action required; run the relevant local quality check for fresh coverage."));
    }
  });
  return issues;
}

function hiddenLeakIssue(
  category: HiddenLeakCategory,
  severity: HiddenLeakIssue["severity"],
  id: string,
  source: string,
  target: string,
  summary: string,
  suggestedAction: string
): HiddenLeakIssue {
  return {
    id,
    category,
    severity,
    source: redactReportText(source),
    target: redactReportText(target),
    safeSummary: redactLeakSummary(summary),
    suggestedAction: redactReportText(suggestedAction),
  };
}

function collectLeakStrings(values: string[], fallback: string): string[] {
  return values.filter(isLeakText).map((value) => value || fallback);
}

function hiddenLeakMarkers(value: unknown): string[] {
  const markers: string[] = [];
  collectHiddenLeakMarkers(value, markers, "root");
  return Array.from(new Set(markers)).slice(0, 20);
}

function collectHiddenLeakMarkers(value: unknown, markers: string[], path: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => collectHiddenLeakMarkers(item, markers, `${path}[${index}]`));
    return;
  }
  if (!value || typeof value !== "object") {
    if (typeof value === "string" && isLeakText(value)) {
      markers.push(`${path}: ${redactLeakSummary(value)}`);
    }
    return;
  }
  Object.entries(value as Record<string, unknown>).forEach(([key, item]) => {
    const nextPath = `${path}.${key}`;
    if (isLeakText(key)) {
      markers.push(`${nextPath}: marker redacted`);
    }
    collectHiddenLeakMarkers(item, markers, nextPath);
  });
}

function isLeakText(value: string): boolean {
  return /(hidden|secret|npc_knowledge|debug memory|state_delta|state_deltas|private|mature|api[_-]?key|provider secret|raw_env|sk-)/i.test(value);
}

function redactLeakSummary(value: string): string {
  return redactReportText(value)
    .replace(/hidden\s+fact[^,.;]*/gi, "hidden fact [redacted]")
    .replace(/npc[_\s-]?knowledge[^,.;]*/gi, "npc_knowledge [redacted]")
    .replace(/private[^,.;]*/gi, "private content [redacted]")
    .replace(/mature[^,.;]*/gi, "mature content [redacted]")
    .replace(/state_delta(s)?[^,.;]*/gi, "raw StateDelta [redacted]")
    .replace(/secret[^,.;]*/gi, "secret [redacted]");
}

function EventLogSafeCard({ event, debugEnabled }: { event: DebugEvent; debugEnabled: boolean }) {
  const eventType = eventLogSafeType(event);
  const actor = eventLogSafeActor(event);
  const sourceModule = eventLogSafeSourceModule(event);
  const tags = eventLogSafeTags(event);
  const visibleSummary = event.visible_to_player
    ? redactReportText(event.result)
    : "Debug-only event. Hidden/debug summary is redacted from normal view.";
  return (
    <details className="timeline-event eventlog-event">
      <summary>
        <span>Turn {event.turn}</span>
        <span>#{event.event_id}</span>
        <EventTypeBadge type={eventType} />
        <span>{actor}</span>
        <span>{event.visible_to_player ? "visible" : "debug-gated"}</span>
      </summary>
      <dl className="event-details">
        <dt>Event id</dt>
        <dd>{event.event_id}</dd>
        <dt>Turn/time</dt>
        <dd>
          Turn {event.turn} / {event.created_at}
        </dd>
        <dt>Type</dt>
        <dd><EventTypeBadge type={eventType} /></dd>
        <dt>Actor</dt>
        <dd>{actor}</dd>
        <dt>Source module</dt>
        <dd>{sourceModule}</dd>
        <dt>Visible summary</dt>
        <dd>{visibleSummary}</dd>
        <dt>Linked StateDelta count</dt>
        <dd>{event.state_deltas.length}</dd>
        <dt>Tags</dt>
        <dd>{tags.length > 0 ? tags.map(redactReportText).join(", ") : "None"}</dd>
      </dl>
      <p className="muted">Raw EventLog JSON and raw StateDelta payloads are hidden from normal view.</p>
      <DebugGate debugEnabled={debugEnabled} title="EventLog Debug Details">
        <details>
          <summary>Raw event JSON and StateDelta details ({event.state_deltas.length})</summary>
          <pre>{JSON.stringify(redactDebugText(event), null, 2)}</pre>
        </details>
      </DebugGate>
    </details>
  );
}

function sortedUnique(values: string[]): string[] {
  return Array.from(new Set(values.filter(Boolean))).sort();
}

function eventLogSafeType(event: DebugEvent): string {
  return event.visible_to_player ? redactReportText(event.action_type) : "debug-gated";
}

function eventLogSafeActor(event: DebugEvent): string {
  return event.visible_to_player ? redactReportText(event.actor_id) : "debug-gated actor";
}

function eventLogSafeSourceModule(event: DebugEvent): string {
  if (!event.visible_to_player) {
    return "debug-gated";
  }
  const metadataSource = event.state_deltas
    .map((delta) => delta.metadata.source || delta.metadata.module || delta.metadata.module_id)
    .find(Boolean);
  if (metadataSource) {
    return redactReportText(metadataSource);
  }
  const [prefix] = event.action_type.split("_");
  return prefix || "core";
}

function eventLogSafeTags(event: DebugEvent): string[] {
  if (!event.visible_to_player) {
    return ["debug-gated"];
  }
  const tags = new Set<string>();
  event.state_deltas.forEach((delta) => {
    Object.entries(delta.metadata).forEach(([key, value]) => {
      const lowerKey = key.toLowerCase();
      if (lowerKey === "tag" || lowerKey === "tags" || lowerKey === "event_tag") {
        value
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean)
          .forEach((tag) => tags.add(redactReportText(tag)));
      }
    });
  });
  if (event.visible_to_player) {
    tags.add("player-visible");
  } else {
    tags.add("debug-gated");
  }
  return Array.from(tags).sort();
}

type StateDeltaViewerRow = {
  id: string;
  eventId: string;
  turn: number;
  eventType: string;
  actorId: string;
  sourceModule: string;
  op: string;
  path: string;
  valueSummary: string;
  applyStatus: string;
};

function StateDeltaViewerPanel({ events }: { events: DebugEvent[] }) {
  const [opFilter, setOpFilter] = useState("");
  const [pathPrefix, setPathPrefix] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [turnFrom, setTurnFrom] = useState("");
  const [turnTo, setTurnTo] = useState("");
  const [pathSearch, setPathSearch] = useState("");
  const rows = useMemo(() => flattenStateDeltaRows(events), [events]);
  const ops = useMemo(() => sortedUnique(rows.map((row) => row.op)), [rows]);
  const eventTypes = useMemo(() => sortedUnique(rows.map((row) => row.eventType)), [rows]);
  const filteredRows = useMemo(
    () =>
      rows.filter((row) => {
        const from = turnFrom ? Number(turnFrom) : null;
        const to = turnTo ? Number(turnTo) : null;
        if (opFilter && row.op !== opFilter) return false;
        if (eventTypeFilter && row.eventType !== eventTypeFilter) return false;
        if (from !== null && row.turn < from) return false;
        if (to !== null && row.turn > to) return false;
        if (pathPrefix && !row.path.startsWith(pathPrefix)) return false;
        if (pathSearch && !row.path.toLowerCase().includes(pathSearch.toLowerCase())) return false;
        return true;
      }),
    [eventTypeFilter, opFilter, pathPrefix, pathSearch, rows, turnFrom, turnTo]
  );

  return (
    <section className="debug-group statedelta-viewer">
      <div className="authoring-pane-header">
        <div>
          <h2>StateDelta Viewer Pro</h2>
          <p className="muted">
            Debug-only StateDelta inspection. This viewer is read-only and cannot apply deltas or modify GameState.
          </p>
        </div>
        <span className="badge">ENABLE_DEBUG_API required</span>
      </div>
      <div className="timeline-controls">
        <label>
          Op
          <select value={opFilter} onChange={(event) => setOpFilter(event.target.value)}>
            <option value="">All ops</option>
            {ops.map((op) => (
              <option key={op} value={op}>
                {op}
              </option>
            ))}
          </select>
        </label>
        <label>
          Path prefix
          <input value={pathPrefix} placeholder="player." onChange={(event) => setPathPrefix(event.target.value)} />
        </label>
        <label>
          Path search
          <input value={pathSearch} placeholder="inventory" onChange={(event) => setPathSearch(event.target.value)} />
        </label>
        <label>
          Event type
          <select value={eventTypeFilter} onChange={(event) => setEventTypeFilter(event.target.value)}>
            <option value="">All types</option>
            {eventTypes.map((eventType) => (
              <option key={eventType} value={eventType}>
                {eventType}
              </option>
            ))}
          </select>
        </label>
        <label>
          Turn from
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            value={turnFrom}
            placeholder="start"
            onChange={(event) => setTurnFrom(event.target.value.replace(/\D/g, ""))}
          />
        </label>
        <label>
          Turn to
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            value={turnTo}
            placeholder="end"
            onChange={(event) => setTurnTo(event.target.value.replace(/\D/g, ""))}
          />
        </label>
      </div>
      {rows.length === 0 ? (
        <EmptyState title="No StateDelta rows loaded." detail="Load a session or save EventLog first. StateDelta debug details remain gated." />
      ) : filteredRows.length === 0 ? (
        <EmptyState title="No StateDelta rows match these filters." detail="Try another op, path prefix, event type, or turn range." />
      ) : (
        <div className="debug-event-list">
          {filteredRows.map((row) => (
            <details className="timeline-event statedelta-row" key={row.id}>
              <summary>
                <span>Turn {row.turn}</span>
                <StateDeltaOpBadge op={row.op} />
                <span>{row.path}</span>
                <span>{row.eventId}</span>
              </summary>
              <dl className="event-details">
                <dt>Event id</dt>
                <dd>{row.eventId}</dd>
                <dt>Delta op</dt>
                <dd><StateDeltaOpBadge op={row.op} /></dd>
                <dt>Path</dt>
                <dd>{row.path}</dd>
                <dt>Value summary</dt>
                <dd>{row.valueSummary}</dd>
                <dt>Apply status</dt>
                <dd>{row.applyStatus}</dd>
                <dt>Source action/module</dt>
                <dd>
                  {row.eventType} / {row.sourceModule}
                </dd>
                <dt>Actor</dt>
                <dd>{row.actorId}</dd>
              </dl>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}

function flattenStateDeltaRows(events: DebugEvent[]): StateDeltaViewerRow[] {
  return events.flatMap((event) =>
    event.state_deltas.map((delta, index) => ({
      id: `${event.event_id}-${index}`,
      eventId: event.event_id,
      turn: event.turn,
      eventType: redactReportText(event.action_type),
      actorId: redactReportText(event.actor_id),
      sourceModule: redactReportText(delta.metadata.source || delta.metadata.module || delta.metadata.module_id || eventLogSafeSourceModule(event)),
      op: redactReportText(delta.operation),
      path: redactStateDeltaPath(delta.path),
      valueSummary: summarizeStateDeltaValue(delta.value),
      applyStatus: delta.caused_by_event_id || event.event_id ? "recorded in EventLog" : "recorded",
    }))
  );
}

function summarizeStateDeltaValue(value: unknown): string {
  if (value === undefined) {
    return "not provided";
  }
  const redacted = redactDebugText(value);
  if (redacted === null || typeof redacted === "boolean" || typeof redacted === "number") {
    return String(redacted);
  }
  if (typeof redacted === "string") {
    return redactReportText(redacted).length > 80 ? `${redactReportText(redacted).slice(0, 77)}...` : redactReportText(redacted);
  }
  if (Array.isArray(redacted)) {
    return `array(${redacted.length})`;
  }
  if (redacted && typeof redacted === "object") {
    return `object(${Object.keys(redacted as Record<string, unknown>).length} keys)`;
  }
  return "redacted";
}

function redactStateDeltaPath(path: string): string {
  return redactReportText(path.replace(/secrets?\.[^.]+/gi, "secrets.[redacted]"));
}

const VISIBLE_DEBUG_COMPARE_SECTIONS = ["facts", "NPCs", "inventory", "quests", "modules", "timeline"] as const;
type VisibleDebugCompareSection = (typeof VISIBLE_DEBUG_COMPARE_SECTIONS)[number];

function VisibleDebugStateCompare({
  visibleState,
  events,
  saves,
  modules,
  lastResponse
}: {
  visibleState: VisibleState | null;
  events: DebugEvent[];
  saves: SaveSummary[];
  modules: ModuleDebugSummary[];
  lastResponse: unknown;
}) {
  const [section, setSection] = useState<VisibleDebugCompareSection>("facts");
  const report = useMemo(
    () => buildVisibleDebugCompareReport(visibleState, events, saves, modules, lastResponse),
    [events, lastResponse, modules, saves, visibleState]
  );
  const selected = report.sections[section];

  return (
    <section className="debug-group visible-debug-compare">
      <div className="authoring-pane-header">
        <div>
          <h2>Visible vs Debug State Compare</h2>
          <p className="muted">
            ENABLE_DEBUG_API required. Debug-gated boundary check for visible_state filtering. Hidden text is summarized and redacted by default.
          </p>
        </div>
        <span className="badge">Debug only</span>
      </div>
      <div className="timeline-controls">
        <label>
          Compare section
          <select value={section} onChange={(event) => setSection(event.target.value as VisibleDebugCompareSection)}>
            {VISIBLE_DEBUG_COMPARE_SECTIONS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
      </div>
      {!visibleState ? (
        <EmptyState title="No visible_state loaded." detail="Start or load a world session before comparing visibility boundaries." />
      ) : (
        <>
          <div className="comparison-grid">
            <section className="section-card player">
              <h3>visible_state: {section}</h3>
              <dl className="event-details">
                <dt>Visible count</dt>
                <dd>{selected.visibleCount}</dd>
                <dt>Safe examples</dt>
                <dd>{selected.safeExamples.length > 0 ? selected.safeExamples.join(", ") : "None"}</dd>
              </dl>
            </section>
            <section className="section-card">
              <h3>debug/raw summary: {section}</h3>
              <dl className="event-details">
                <dt>Debug count</dt>
                <dd>{selected.debugCount}</dd>
                <dt>Filtered count</dt>
                <dd>{selected.filteredCount}</dd>
                <dt>Redacted summary</dt>
                <dd>{selected.redactedSummary}</dd>
              </dl>
            </section>
          </div>
          <div className="timeline-summary">
            <span>{report.filteredFieldCount} filtered field markers</span>
            <span>{report.rawDeltaCount} raw StateDelta records gated</span>
            <span>{report.debugOnlyEventCount} debug-only events gated</span>
            <span>{report.lastResponseKeyCount} last response keys summarized</span>
          </div>
          <section className="section-card">
            <h3>Visibility Rule Warnings</h3>
            {report.warnings.length === 0 ? (
              <p className="muted">No visibility warning markers found in visible_state safe summary.</p>
            ) : (
              <ul className="compact-list">
                {report.warnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </section>
  );
}

function buildVisibleDebugCompareReport(
  visibleState: VisibleState | null,
  events: DebugEvent[],
  saves: SaveSummary[],
  modules: ModuleDebugSummary[],
  lastResponse: unknown
): {
  sections: Record<VisibleDebugCompareSection, {
    visibleCount: number;
    debugCount: number;
    filteredCount: number;
    safeExamples: string[];
    redactedSummary: string;
  }>;
  filteredFieldCount: number;
  rawDeltaCount: number;
  debugOnlyEventCount: number;
  lastResponseKeyCount: number;
  warnings: string[];
} {
  const visibleFacts = visibleState?.known_facts ?? [];
  const visibleNpcs = visibleState?.visible_npcs ?? [];
  const inventory = visibleState?.inventory ?? [];
  const quests = visibleState?.quests ?? [];
  const rawDeltaCount = events.reduce((total, event) => total + event.state_deltas.length, 0);
  const debugOnlyEventCount = events.filter((event) => !event.visible_to_player).length;
  const filteredFieldCount =
    countSensitiveMarkers(visibleState) +
    countSensitiveMarkers(events.map((event) => event.state_deltas)) +
    countSensitiveMarkers(lastResponse);
  const lastResponseKeyCount = lastResponse && typeof lastResponse === "object" ? Object.keys(lastResponse as Record<string, unknown>).length : 0;
  const hiddenDeltaCount = events.reduce(
    (total, event) => total + event.state_deltas.filter((delta) => !event.visible_to_player && delta.metadata.visible_to_player !== "true").length,
    0
  );
  const warnings = buildVisibilityWarnings(visibleState);

  return {
    sections: {
      facts: {
        visibleCount: visibleFacts.length,
        debugCount: visibleFacts.length + hiddenDeltaCount,
        filteredCount: hiddenDeltaCount,
        safeExamples: visibleFacts.slice(0, 5).map((fact) => redactReportText(fact.id)),
        redactedSummary: `${hiddenDeltaCount} debug-only fact/path marker(s) redacted`,
      },
      NPCs: {
        visibleCount: visibleNpcs.length,
        debugCount: visibleNpcs.length + debugOnlyEventCount,
        filteredCount: debugOnlyEventCount,
        safeExamples: visibleNpcs.slice(0, 5).map((npc) => redactReportText(npc.id)),
        redactedSummary: "NPC secrets and npc_knowledge are not displayed; debug-only actor details are grouped.",
      },
      inventory: {
        visibleCount: inventory.length,
        debugCount: inventory.length + events.filter((event) => event.state_deltas.some((delta) => delta.path.includes("objects") || delta.path.includes("inventory"))).length,
        filteredCount: events.filter((event) => !event.visible_to_player && event.state_deltas.some((delta) => delta.path.includes("objects") || delta.path.includes("inventory"))).length,
        safeExamples: inventory.slice(0, 5).map((item) => redactReportText(item.id)),
        redactedSummary: "Hidden item properties are summarized by count only.",
      },
      quests: {
        visibleCount: quests.length,
        debugCount: quests.length + events.filter((event) => event.action_type.includes("quest") || event.state_deltas.some((delta) => delta.path.includes("quest"))).length,
        filteredCount: events.filter((event) => !event.visible_to_player && (event.action_type.includes("quest") || event.state_deltas.some((delta) => delta.path.includes("quest")))).length,
        safeExamples: quests.slice(0, 5).map((quest) => redactReportText(quest.id)),
        redactedSummary: "Hidden objectives/truth are not printed; quest debug changes are counted.",
      },
      modules: {
        visibleCount: Number(Boolean(visibleState?.active_combat)),
        debugCount: modules.length,
        filteredCount: modules.filter((module) => module.hidden_details_redacted).length,
        safeExamples: modules.slice(0, 5).map((module) => redactReportText(module.module_id)),
        redactedSummary: "Module debug state is summarized by status; hidden module internals are not shown.",
      },
      timeline: {
        visibleCount: events.filter((event) => event.visible_to_player).length,
        debugCount: events.length,
        filteredCount: debugOnlyEventCount,
        safeExamples: events.filter((event) => event.visible_to_player).slice(0, 5).map((event) => redactReportText(event.event_id)),
        redactedSummary: `${rawDeltaCount} raw StateDelta record(s) require debug-gated viewers.`,
      },
    },
    filteredFieldCount,
    rawDeltaCount,
    debugOnlyEventCount,
    lastResponseKeyCount,
    warnings,
  };
}

function countSensitiveMarkers(value: unknown): number {
  if (Array.isArray(value)) {
    return value.reduce((total, item) => total + countSensitiveMarkers(item), 0);
  }
  if (!value || typeof value !== "object") {
    return typeof value === "string" && /(api[_-]?key|secret|hidden|npc_knowledge|state_delta|raw_env)/i.test(value) ? 1 : 0;
  }
  return Object.entries(value as Record<string, unknown>).reduce((total, [key, item]) => {
    const keyHit = /(api[_-]?key|secret|hidden|npc_knowledge|debug|state_delta|raw_env)/i.test(key) ? 1 : 0;
    return total + keyHit + countSensitiveMarkers(item);
  }, 0);
}

function buildVisibilityWarnings(visibleState: VisibleState | null): string[] {
  if (!visibleState) {
    return [];
  }
  const serialized = JSON.stringify(redactDebugText(visibleState)).toLowerCase();
  const warnings: string[] = [];
  if (serialized.includes("api_key") || serialized.includes("sk-")) {
    warnings.push("Potential API key marker found in visible_state summary.");
  }
  if (serialized.includes("npc_knowledge")) {
    warnings.push("npc_knowledge marker found in visible_state summary.");
  }
  if (serialized.includes("state_delta")) {
    warnings.push("raw StateDelta marker found in visible_state summary.");
  }
  if (serialized.includes("secret") || serialized.includes("hidden")) {
    warnings.push("hidden/secret marker found in visible_state summary; inspect source visibility rules.");
  }
  return warnings;
}

function GameplayModuleDebugger({
  modules,
  selectedModuleId,
  detail,
  dryRun,
  error,
  onSelectModule,
  onRefresh,
  onDryRun,
  disabled
}: {
  modules: ModuleDebugSummary[];
  selectedModuleId: string;
  detail: ModuleDebugSummary | null;
  dryRun: ModuleActionDryRunResponse | null;
  error: string;
  onSelectModule: (moduleId: string) => void;
  onRefresh: () => void;
  onDryRun: (actionId: string) => void;
  disabled: boolean;
}) {
  const selectedActionId = detail?.actions[0]?.id ?? "";
  return (
    <section className="debug-group gameplay-module-debugger">
      <header className="panel-header">
        <div>
          <h2>Gameplay Module Debugger</h2>
          <p className="muted">ENABLE_DEBUG_API required. Local debug only. Dry-run previews StateDelta/Event output without applying it.</p>
        </div>
        <button type="button" onClick={onRefresh} disabled={disabled}>Refresh</button>
      </header>
      {error && <p className="error">{error}</p>}
      {error.toLowerCase().includes("debug") && <p className="muted">debug disabled</p>}
      {modules.length === 0 && !error ? (
        <p className="muted">No gameplay modules discovered.</p>
      ) : (
        <div className="form-row">
          <label>
            Module
            <select value={selectedModuleId} onChange={(event) => onSelectModule(event.target.value)} disabled={disabled}>
              {modules.map((module) => (
                <option key={module.module_id} value={module.module_id}>{module.name}</option>
              ))}
            </select>
          </label>
        </div>
      )}
      {detail && (
        <div className="debug-grid">
          <dl>
            <dt>Module</dt>
            <dd>{detail.module_id}</dd>
            <dt>Version</dt>
            <dd>{detail.version}</dd>
            <dt>Type</dt>
            <dd>{detail.module_type}</dd>
            <dt>Calls LLM</dt>
            <dd>{detail.calls_llm ? "yes" : "no"}</dd>
            <dt>Hidden details</dt>
            <dd>{detail.hidden_details_redacted ? "redacted" : "debug"}</dd>
          </dl>
          <div>
            <h3>Actions</h3>
            <ItemList
              emptyText="No declarative actions."
              items={detail.actions.map((action) => (
                <div key={action.id}>
                  <strong>{action.label}</strong>
                  <span className="muted"> {action.id}</span>
                  <button type="button" onClick={() => onDryRun(action.id)} disabled={disabled}>Dry-run</button>
                  <AuthoringPreviewCode content={JSON.stringify({
                    aliases: action.aliases,
                    target_types: action.target_types,
                    preconditions: action.precondition_count,
                    checks: action.check_count,
                    state_delta_templates: action.state_delta_templates
                  }, null, 2)} />
                </div>
              ))}
            />
          </div>
          <div>
            <h3>Permissions</h3>
            <AuthoringPreviewCode content={JSON.stringify(detail.permissions, null, 2)} />
          </div>
          <div>
            <h3>State Extensions</h3>
            <AuthoringPreviewCode content={JSON.stringify(detail.state_schema_extensions, null, 2)} />
          </div>
        </div>
      )}
      {dryRun && (
        <div>
          <h3>Dry-run Result</h3>
          <dl>
            <dt>Action</dt>
            <dd>{dryRun.action_id}</dd>
            <dt>Outcome</dt>
            <dd>{dryRun.selected_outcome}</dd>
            <dt>State unchanged</dt>
            <dd>{dryRun.state_unchanged ? "yes" : "no"}</dd>
            <dt>Hidden facts</dt>
            <dd>{dryRun.hidden_facts_redacted ? "redacted" : "debug"}</dd>
          </dl>
          <AuthoringPreviewCode content={JSON.stringify({
            preconditions: dryRun.preconditions_result,
            checks: dryRun.checks_result,
            state_delta_preview: dryRun.state_delta_preview,
            event_preview: dryRun.event_preview,
            visibility_summary: dryRun.visibility_summary
          }, null, 2)} />
        </div>
      )}
      {!selectedActionId && detail && <p className="muted">No action available for dry-run.</p>}
    </section>
  );
}

function CrashReportViewer({
  reports,
  selectedReportId,
  selectedReport,
  error,
  onRefresh,
  onSelect,
  onDelete
}: {
  reports: CrashReport[];
  selectedReportId: string;
  selectedReport: CrashReport | null;
  error: string;
  onRefresh: () => void;
  onSelect: (reportId: string) => void;
  onDelete: (reportId: string) => void;
}) {
  return (
    <section className="debug-group crash-report-viewer">
      <header className="panel-header">
        <div>
          <h2>Crash Report Viewer</h2>
          <p className="muted">Local reports only. Details are redacted and never uploaded.</p>
        </div>
        <button type="button" onClick={onRefresh}>Refresh</button>
      </header>
      {error && <p className="error">{error}</p>}
      {error.toLowerCase().includes("debug") && <p className="muted">debug disabled</p>}
      {reports.length === 0 && !error ? (
        <p className="muted">No local crash reports recorded.</p>
      ) : (
        <div className="form-row">
          <label>
            Report
            <select value={selectedReportId} onChange={(event) => onSelect(event.target.value)}>
              {reports.map((report) => (
                <option key={report.id} value={report.id}>
                  {report.timestamp} - {report.component} - {report.error_type}
                </option>
              ))}
            </select>
          </label>
        </div>
      )}
      {selectedReport && (
        <div className="debug-grid">
          <dl>
            <dt>Component</dt>
            <dd>{selectedReport.component}</dd>
            <dt>Error</dt>
            <dd>{selectedReport.error_type}</dd>
            <dt>Timestamp</dt>
            <dd>{selectedReport.timestamp}</dd>
            <dt>Message</dt>
            <dd>{selectedReport.safe_message}</dd>
          </dl>
          <div>
            <h3>Context</h3>
            <pre>{JSON.stringify(selectedReport.context_safe_summary, null, 2)}</pre>
          </div>
          <div>
            <h3>Redacted Stack</h3>
            <pre>{selectedReport.stack_redacted}</pre>
          </div>
          <div className="authoring-action-bar">
            <button type="button" onClick={() => onDelete(selectedReport.id)}>
              Delete Local Report
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function NPCSimulationDebugger({
  summaries,
  selectedNPCId,
  detail,
  events,
  dryRun,
  behaviorTimeline,
  behaviorTimelineError,
  behaviorTurnFrom,
  behaviorTurnTo,
  behaviorFilter,
  error,
  onSelectNPC,
  onRefresh,
  onDryRun,
  onRefreshBehaviorTimeline,
  onBehaviorTurnFromChange,
  onBehaviorTurnToChange,
  onBehaviorFilterChange,
  disabled
}: {
  summaries: DebugNPCSimulationSummary[];
  selectedNPCId: string;
  detail: DebugNPCSimulationDetail | null;
  events: DebugEvent[];
  dryRun: DebugNPCSimulationDryRunResponse | null;
  behaviorTimeline: NPCBehaviorTimelineResponse | null;
  behaviorTimelineError: string;
  behaviorTurnFrom: string;
  behaviorTurnTo: string;
  behaviorFilter: string;
  error: string;
  onSelectNPC: (npcId: string) => void;
  onRefresh: () => void;
  onDryRun: () => void;
  onRefreshBehaviorTimeline: () => void;
  onBehaviorTurnFromChange: (value: string) => void;
  onBehaviorTurnToChange: (value: string) => void;
  onBehaviorFilterChange: (value: string) => void;
  disabled: boolean;
}) {
  const activePlan = detail?.plans.find((plan) => String(plan.status ?? "") === "active") ?? detail?.plans[0] ?? null;
  const currentStep = activePlan && Array.isArray(activePlan.steps)
    ? activePlan.steps[Number(activePlan.current_step_index ?? 0)] ?? null
    : null;
  const behaviorTypes = Array.from(new Set(behaviorTimeline?.entries.map((entry) => entry.behavior_type) ?? [])).sort();
  const visibleBehaviorEntries = behaviorTimeline?.entries.filter((entry) => behaviorFilter === "all" || entry.behavior_type === behaviorFilter) ?? [];
  return (
    <section className="debug-group npc-simulation-debugger">
      <h2>NPC Simulation</h2>
      <div className="timeline-controls">
        <label>
          NPC
          <select value={selectedNPCId} onChange={(event) => onSelectNPC(event.target.value)} disabled={disabled || summaries.length === 0}>
            <option value="">Select NPC</option>
            {summaries.map((npc) => (
              <option key={npc.npc_id} value={npc.npc_id}>
                {npc.npc_id}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={onRefresh} disabled={disabled}>Refresh</button>
        <button type="button" onClick={onDryRun} disabled={disabled}>Dry-run Tick</button>
      </div>
      {error && <p className="error">{sanitizeDisplayError(error)}</p>}
      {error.toLowerCase().includes("debug") && <p className="muted">debug disabled</p>}
      {summaries.length === 0 && !error && (
        <EmptyState title="No NPC simulation state." detail="Start a session, then refresh this local debug panel." />
      )}
      {detail && (
        <div className="npc-sim-grid">
          <DashboardCard title="Condition" value={`${detail.condition}${detail.alive ? "" : " / inactive"}`}>
            <p>Location: {detail.location_id}</p>
          </DashboardCard>
          <DashboardCard title="Goals" value={detail.active_goal_id ?? "none"}>
            <SafeJSON value={detail.goals} />
          </DashboardCard>
          <DashboardCard title="Intent queue" value={String(detail.intent_count)}>
            <SafeJSON value={detail.intent_queue} />
          </DashboardCard>
          <DashboardCard title="Active plan" value={activePlan ? String(activePlan.id ?? "plan") : "none"}>
            <SafeJSON value={{ plan: activePlan, current_step: currentStep }} />
          </DashboardCard>
          <DashboardCard title="Known facts" value={String(detail.known_fact_ids.length)}>
            <p>{detail.known_fact_ids.length ? detail.known_fact_ids.join(", ") : "None"}</p>
            {detail.hidden_fact_ids.length > 0 && <p className="muted">Hidden ids: {detail.hidden_fact_ids.join(", ")}</p>}
          </DashboardCard>
          <DashboardCard title="Disposition" value="debug">
            <SafeJSON value={{
              emotional_state: detail.emotional_state,
              social_disposition: detail.social_disposition,
              faction_duties: detail.faction_duties,
              relationship_behavior_summary: detail.relationship_behavior_summary
            }} />
          </DashboardCard>
          <DashboardCard title="Decision reasons" value={String(detail.debug_reason_count)}>
            <SafeJSON value={detail.debug_decision_reasons} />
          </DashboardCard>
          <DashboardCard title="Rumors / crimes" value={`${detail.known_rumor_ids.length} / ${detail.known_crime_ids.length}`}>
            <p>Rumors: {detail.known_rumor_ids.join(", ") || "None"}</p>
            <p>Crimes: {detail.known_crime_ids.join(", ") || "None"}</p>
          </DashboardCard>
        </div>
      )}
      <h3>Recent Simulation Events</h3>
      <DebugEventSummary events={events.slice(0, 8)} emptyText="No NPC simulation events yet." />
      <h3>Behavior Timeline</h3>
      <div className="timeline-controls">
        <label>
          From
          <input type="number" value={behaviorTurnFrom} onChange={(event) => onBehaviorTurnFromChange(event.target.value)} disabled={disabled} />
        </label>
        <label>
          To
          <input type="number" value={behaviorTurnTo} onChange={(event) => onBehaviorTurnToChange(event.target.value)} disabled={disabled} />
        </label>
        <label>
          Type
          <select value={behaviorFilter} onChange={(event) => onBehaviorFilterChange(event.target.value)} disabled={disabled}>
            <option value="all">All</option>
            {behaviorTypes.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <button type="button" onClick={onRefreshBehaviorTimeline} disabled={disabled || !selectedNPCId}>Load Timeline</button>
      </div>
      {behaviorTimelineError && <p className="error">{sanitizeDisplayError(behaviorTimelineError)}</p>}
      {behaviorTimelineError.toLowerCase().includes("debug") && <p className="muted">debug disabled</p>}
      {visibleBehaviorEntries.length === 0 ? (
        <p className="muted">No NPC behavior timeline entries.</p>
      ) : (
        <div className="debug-event-list">
          {visibleBehaviorEntries.map((entry) => (
            <details className="timeline-event" key={`${entry.event_id}-${entry.behavior_type}`}>
              <summary>
                <span>Turn {entry.turn}</span>
                <span>{entry.behavior_type}</span>
                <span>{entry.safe_summary}</span>
              </summary>
              <SafeJSON value={entry} />
            </details>
          ))}
        </div>
      )}
      {dryRun && (
        <details className="timeline-event">
          <summary>
            <span>Dry-run</span>
            <span>{dryRun.state_unchanged ? "state unchanged" : "changed"}</span>
          </summary>
          <SafeJSON value={dryRun.result} />
        </details>
      )}
    </section>
  );
}

function SafeJSON({ value }: { value: unknown }) {
  return <pre>{JSON.stringify(redactDebugText(value), null, 2)}</pre>;
}

function redactDebugText(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map((item) => redactDebugText(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => {
        const lower = key.toLowerCase();
        if (lower.includes("api_key") || lower.includes("raw_env") || lower.includes("secret")) {
          return [key, "[redacted]"];
        }
        if (lower === "text" || lower === "content" || lower === "narrative_text") {
          return [key, "[redacted text]"];
        }
        return [key, redactDebugText(item)];
      })
    );
  }
  if (typeof value === "string" && /sk-[A-Za-z0-9_-]+/.test(value)) {
    return "sk-[redacted]";
  }
  return value;
}

function TimelineReplayPanel({
  timeline,
  source,
  selectedSaveId,
  selectedFilter,
  onFilterChange,
  onLoadSession,
  onLoadSave,
  onDryRun,
  error,
  dryRun,
  dryRunError,
  debugEnabled
}: {
  timeline: TimelineReplayResponse | null;
  source: "session" | "save";
  selectedSaveId: string;
  selectedFilter: TimelineFilter;
  onFilterChange: (filter: TimelineFilter) => void;
  onLoadSession: () => void;
  onLoadSave: () => void;
  onDryRun: () => void;
  error: string;
  dryRun: TimelineReplayResponse | null;
  dryRunError: string;
  debugEnabled: boolean;
}) {
  const [actorFilter, setActorFilter] = useState("");
  const [turnFrom, setTurnFrom] = useState("");
  const [turnTo, setTurnTo] = useState("");
  const [jumpTurn, setJumpTurn] = useState("");
  const [currentTurnIndex, setCurrentTurnIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const filteredTurns = useMemo(
    () =>
      filterTimelineTurns(timeline, {
        eventType: selectedFilter,
        actor: actorFilter,
        turnFrom,
        turnTo,
        visibleOnly: true
      }),
    [timeline, selectedFilter, actorFilter, turnFrom, turnTo]
  );
  const replaySummary = dryRun?.replay_summary ?? timeline?.replay_summary ?? null;
  const eventCount = filteredTurns.reduce((total, turnGroup) => total + turnGroup.events.length, 0);
  const deltaCount = filteredTurns.reduce(
    (total, turnGroup) =>
      total + turnGroup.events.reduce((turnTotal, event) => turnTotal + event.delta_count, 0),
    0
  );
  const actorOptions = useMemo(() => {
    const actors = new Set<string>();
    timeline?.turns.forEach((turnGroup) => {
      turnGroup.events.forEach((event) => actors.add(event.actor_id));
    });
    return Array.from(actors).sort();
  }, [timeline]);
  const currentTurn = filteredTurns[currentTurnIndex] ?? null;

  useEffect(() => {
    setCurrentTurnIndex(0);
    setIsPlaying(false);
  }, [timeline, selectedFilter, actorFilter, turnFrom, turnTo]);

  useEffect(() => {
    if (!isPlaying || filteredTurns.length <= 1) {
      return;
    }
    const timer = window.setInterval(() => {
      setCurrentTurnIndex((index) => {
        if (index >= filteredTurns.length - 1) {
          setIsPlaying(false);
          return index;
        }
        return index + 1;
      });
    }, 1200);
    return () => window.clearInterval(timer);
  }, [filteredTurns.length, isPlaying]);

  function handlePrevious() {
    setIsPlaying(false);
    setCurrentTurnIndex((index) => Math.max(0, index - 1));
  }

  function handleNext() {
    setCurrentTurnIndex((index) => Math.min(Math.max(filteredTurns.length - 1, 0), index + 1));
  }

  function handleJumpToTurn() {
    setIsPlaying(false);
    const targetTurn = Number(jumpTurn || currentTurn?.turn || 0);
    const index = filteredTurns.findIndex((turnGroup) => turnGroup.turn >= targetTurn);
    if (index >= 0) {
      setCurrentTurnIndex(index);
    }
  }

  return (
    <section className="debug-group timeline-replay">
      <div className="authoring-pane-header">
        <div>
          <h2>Timeline Replay UI Pro</h2>
          <p className="muted">
            Visible replay view shows player-safe event summaries. Raw StateDelta details are debug-gated and read-only.
          </p>
        </div>
        <StatusBadge label={debugEnabled ? "Debug details gated on" : "Debug details disabled"} enabled={debugEnabled} />
      </div>
      <div className="timeline-controls">
        <label>
          Replay source
          <select value={source} disabled>
            <option value="session">Session</option>
            <option value="save">Save</option>
          </select>
        </label>
        <label>
          Event type
          <select value={selectedFilter} onChange={(event) => onFilterChange(event.target.value as TimelineFilter)}>
            {TIMELINE_FILTERS.map((filter) => (
              <option key={filter} value={filter}>
                {filter}
              </option>
            ))}
          </select>
        </label>
        <label>
          Actor
          <select value={actorFilter} onChange={(event) => setActorFilter(event.target.value)}>
            <option value="">All actors</option>
            {actorOptions.map((actor) => (
              <option key={actor} value={actor}>
                {actor}
              </option>
            ))}
          </select>
        </label>
        <label>
          Turn from
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="start"
            value={turnFrom}
            onChange={(event) => setTurnFrom(event.target.value.replace(/\D/g, ""))}
          />
        </label>
        <label>
          Turn to
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="end"
            value={turnTo}
            onChange={(event) => setTurnTo(event.target.value.replace(/\D/g, ""))}
          />
        </label>
        <label className="checkbox-row">
          <input type="checkbox" checked readOnly />
          Visible/system-safe replay only
        </label>
        <button type="button" onClick={onLoadSession}>
          Session Replay
        </button>
        <button type="button" onClick={onLoadSave} disabled={!selectedSaveId}>
          Save Replay
        </button>
        <button type="button" onClick={onDryRun} disabled={!selectedSaveId}>
          Replay Dry-Run
        </button>
      </div>
      <div className="timeline-controls replay-controls" aria-label="Replay controls">
        <button type="button" onClick={() => setIsPlaying(true)} disabled={!filteredTurns.length}>
          Start
        </button>
        <button type="button" onClick={handlePrevious} disabled={!filteredTurns.length || currentTurnIndex === 0}>
          Previous
        </button>
        <button type="button" onClick={handleNext} disabled={!filteredTurns.length || currentTurnIndex >= filteredTurns.length - 1}>
          Next
        </button>
        <label>
          Jump turn
          <input
            inputMode="numeric"
            pattern="[0-9]*"
            placeholder="turn"
            value={jumpTurn}
            onChange={(event) => setJumpTurn(event.target.value.replace(/\D/g, ""))}
          />
        </label>
        <button type="button" onClick={handleJumpToTurn} disabled={!filteredTurns.length}>
          Jump to turn
        </button>
        <button type="button" onClick={() => setIsPlaying(false)} disabled={!isPlaying}>
          Pause
        </button>
        <span className="badge">{isPlaying ? "Replay started" : "Replay paused"}</span>
        <span className="badge">Current turn: {currentTurn?.turn ?? "none"}</span>
      </div>
      {error && <p className="error">{error}</p>}
      {error && error.toLowerCase().includes("debug") && <p className="muted">debug disabled</p>}
      {dryRunError && <p className="error">{dryRunError}</p>}
      {timeline ? (
        <>
          <div className="timeline-summary">
            <span>{timeline.source_type}: {timeline.source_id}</span>
            <span>{eventCount} events</span>
            <span>{deltaCount} deltas</span>
            <span>{timeline.turns.length} turns</span>
            <span>visible/system-safe replay only</span>
          </div>
          {replaySummary && <ReplaySummaryView summary={replaySummary} />}
          {filteredTurns.length === 0 ? (
            <EmptyState title="No replay events match this view." detail="Try another event type, actor, or turn range. Hidden/debug-only events stay out of the normal replay view." />
          ) : (
            <div className="timeline-turns">
              {filteredTurns.map((turnGroup) => (
                <section className={`timeline-turn ${currentTurn?.turn === turnGroup.turn ? "active" : ""}`} key={turnGroup.turn}>
                  <h3>
                    Turn {turnGroup.turn}
                    <span>{turnGroup.events.length} events</span>
                    <span>{turnGroup.events.reduce((total, event) => total + event.delta_count, 0)} deltas</span>
                  </h3>
                  {turnGroup.events.map((event) => (
                    <TimelineEventCard event={event} debugEnabled={debugEnabled} key={event.event_id} />
                  ))}
                </section>
              ))}
            </div>
          )}
        </>
      ) : (
        !error && <EmptyState title="No replay data loaded." detail="Load a session replay or save replay. Replay is read-only and never writes GameState or EventLog." />
      )}
    </section>
  );
}

function ReplaySummaryView({ summary }: { summary: NonNullable<TimelineReplayResponse["replay_summary"]> }) {
  return (
    <div className="replay-summary">
      <dl>
        <dt>Replay events</dt>
        <dd>{summary.event_count}</dd>
        <dt>Final checksum</dt>
        <dd>{summary.final_state_checksum.slice(0, 16)}</dd>
        <dt>Failed event</dt>
        <dd>{summary.failed_event_id ?? "None"}</dd>
        <dt>Checkpoints</dt>
        <dd>{summary.checkpoints.length}</dd>
      </dl>
      {summary.invariant_violations.length > 0 ? (
        <div>
          <strong>Invariant violations</strong>
          <ul className="compact-list">
            {summary.invariant_violations.map((violation) => (
              <li key={violation}>{violation}</li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted">No invariant violations reported.</p>
      )}
    </div>
  );
}

function TimelineEventCard({ event, debugEnabled }: { event: TimelineEventView; debugEnabled: boolean }) {
  return (
    <details className={`timeline-event replay-event ${event.event_kind}`}>
      <summary>
        <span>Turn {event.turn}</span>
        <span>#{event.event_id}</span>
        <span>{event.event_kind}</span>
        <span>{event.action_type}</span>
        <span>{event.actor_id}</span>
        <span>{event.result}</span>
      </summary>
      <dl className="event-details">
        <dt>Visible</dt>
        <dd>{event.visible_to_player ? "yes" : event.visible_changes.length > 0 ? "visible changes only" : "debug-gated"}</dd>
        <dt>Target</dt>
        <dd>{event.target_id ?? "None"}</dd>
        <dt>Created</dt>
        <dd>{event.created_at}</dd>
        <dt>State changes</dt>
        <dd>{event.delta_count} debug-gated change(s)</dd>
      </dl>
      <p className="muted">
        Event safe summary only. Hidden facts and raw StateDelta payloads are not shown in normal replay view.
      </p>
      {event.visible_changes.length > 0 && (
        <div>
          <strong>Visible changes</strong>
          <ul className="compact-list">
            {event.visible_changes.map((change, index) => (
              <li key={`${change.path}-${index}`}>
                {change.operation} {change.path}
                {change.reason ? ` (${change.reason})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      <DebugGate debugEnabled={debugEnabled} title="Timeline Replay Debug Details">
        <details>
          <summary>Debug StateDelta details ({event.state_deltas.length})</summary>
          <pre>{JSON.stringify(redactDebugText(event.state_deltas), null, 2)}</pre>
        </details>
      </DebugGate>
    </details>
  );
}

function filterTimelineTurns(
  timeline: TimelineReplayResponse | null,
  filters: {
    eventType: TimelineFilter;
    actor: string;
    turnFrom: string;
    turnTo: string;
    visibleOnly: boolean;
  }
): TimelineReplayResponse["turns"] {
  if (!timeline) {
    return [];
  }
  const from = filters.turnFrom ? Number(filters.turnFrom) : null;
  const to = filters.turnTo ? Number(filters.turnTo) : null;
  return timeline.turns
    .map((turnGroup) => ({
      ...turnGroup,
      events: turnGroup.events.filter((event) => {
        if (from !== null && event.turn < from) return false;
        if (to !== null && event.turn > to) return false;
        if (filters.actor && event.actor_id !== filters.actor) return false;
        if (filters.visibleOnly && !isTimelineEventSafeForNormalReplay(event)) return false;
        return timelineEventMatchesFilter(event, filters.eventType);
      })
    }))
    .filter((turnGroup) => turnGroup.events.length > 0);
}

function isTimelineEventSafeForNormalReplay(event: TimelineEventView): boolean {
  return event.visible_to_player || event.visible_changes.length > 0;
}

function timelineEventMatchesFilter(event: TimelineEventView, filter: TimelineFilter): boolean {
  if (filter === "all") {
    return true;
  }
  if (filter === "combat") {
    return isCombatTimelineEvent(event);
  }
  if (filter === "social") {
    return isSocialTimelineEvent(event);
  }
  if (filter === "system") {
    return event.event_kind === "system" || event.event_kind === "tick";
  }
  return event.event_kind === filter;
}

function isCombatTimelineEvent(event: TimelineEventView): boolean {
  return (
    /combat|attack|defend|flee/i.test(event.action_type) ||
    event.state_deltas.some((delta) => /^(combats|player\.hp|npcs\.[^.]+\.hp)/.test(delta.path))
  );
}

function isSocialTimelineEvent(event: TimelineEventView): boolean {
  return (
    /rumor|crime|reputation|relationship|faction|social/i.test(event.action_type) ||
    event.state_deltas.some((delta) =>
      /^(rumors|crimes|witnesses|relationships|factions|social_flags)/.test(delta.path)
    )
  );
}

function isSocialDebugEvent(event: DebugEvent): boolean {
  const actionType = event.action_type.toLowerCase();
  return (
    actionType.includes("social") ||
    actionType.includes("crime") ||
    actionType.includes("rumor") ||
    actionType.includes("faction") ||
    actionType.includes("relationship") ||
    actionType.includes("reaction") ||
    event.state_deltas.some((delta) =>
      /^(social_consequences|crimes|rumors|factions|witnesses|relationships)\./.test(delta.path)
    )
  );
}

function isCombatDebugEvent(event: DebugEvent): boolean {
  const actionType = event.action_type.toLowerCase();
  return (
    actionType.includes("combat") ||
    actionType.includes("attack") ||
    actionType.includes("defend") ||
    actionType.includes("flee") ||
    actionType.includes("injury") ||
    actionType.includes("death") ||
    event.state_deltas.some((delta) => /^(combats|player\.hp|npcs\.[^.]+\.hp)/.test(delta.path))
  );
}

function filterPlayerGraph(graph: GraphResponse): GraphResponse {
  const nodes = graph.nodes.filter((node) => node.visibility === "player_visible");
  const nodeIds = new Set(nodes.map((node) => node.id));
  const edges = graph.edges.filter(
    (edge) =>
      edge.visibility === "player_visible" &&
      nodeIds.has(edge.source) &&
      nodeIds.has(edge.target)
  );
  return {
    ...graph,
    scope: "player_visible",
    nodes,
    edges
  };
}

function shortLabel(label: string): string {
  return label.length > 12 ? `${label.slice(0, 11)}...` : label;
}

function parseAuthoringEntities(fileName: string, yaml: string): ParsedAuthoringEntity[] {
  const rootKey = ROOT_KEYS[fileName];
  if (!rootKey) {
    return [];
  }
  const lines = yaml.split(/\r?\n/);
  const entities: ParsedAuthoringEntity[] = [];
  let current: ParsedAuthoringEntity | null = null;

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const listMatch = line.match(/^  -\s+([A-Za-z0-9_]+):\s*(.*)$/);
    if (listMatch) {
      if (current) {
        current.endLine = index - 1;
        entities.push(current);
      }
      const firstField = listMatch[1];
      const firstValue = normalizeYamlScalar(listMatch[2]);
      current = {
        id: firstField === "id" && firstValue ? firstValue : `item-${entities.length + 1}`,
        startLine: index,
        endLine: index,
        fields: { [firstField]: firstValue }
      };
      continue;
    }

    if (!current) {
      continue;
    }

    const fieldMatch = line.match(/^    ([A-Za-z0-9_]+):\s*(.*)$/);
    if (fieldMatch) {
      const fieldName = fieldMatch[1];
      const fieldValue = normalizeYamlScalar(fieldMatch[2]);
      current.fields[fieldName] = fieldValue;
      if (fieldName === "id" && fieldValue) {
        current.id = fieldValue;
      }
    }
  }

  if (current) {
    current.endLine = lines.length - 1;
    entities.push(current);
  }
  return entities;
}

function updateEntityField(
  yaml: string,
  entity: ParsedAuthoringEntity,
  fieldName: string,
  value: string
): string {
  const lines = yaml.split(/\r?\n/);
  const inlineIdPattern = new RegExp(`^(\\s*-\\s+${escapeRegExp(fieldName)}:\\s*).*$`);
  const fieldPattern = new RegExp(`^(\\s{4}${escapeRegExp(fieldName)}:\\s*).*$`);
  const serialized = serializeYamlScalar(value);

  for (let index = entity.startLine; index <= entity.endLine && index < lines.length; index += 1) {
    if (inlineIdPattern.test(lines[index])) {
      lines[index] = lines[index].replace(inlineIdPattern, `$1${serialized}`);
      return lines.join("\n");
    }
    if (fieldPattern.test(lines[index])) {
      lines[index] = lines[index].replace(fieldPattern, `$1${serialized}`);
      return lines.join("\n");
    }
  }

  const insertAt = Math.min(entity.endLine + 1, lines.length);
  lines.splice(insertAt, 0, `    ${fieldName}: ${serialized}`);
  return lines.join("\n");
}

function normalizeYamlScalar(value: string): string {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1);
  }
  return trimmed;
}

function serializeYamlScalar(value: string): string {
  if (value === "true" || value === "false" || /^-?\d+(\.\d+)?$/.test(value)) {
    return value;
  }
  if (value === "") {
    return '""';
  }
  if (/[:#\n\r]/.test(value)) {
    return JSON.stringify(value);
  }
  return value;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function fileCategoryLabel(fileName: string): string {
  if (fileName === "manifest.yaml" || fileName === "mod.yaml") {
    return "mod manifest";
  }
  if (fileName === "items.yaml") {
    return "items / economy fields";
  }
  return fileName.replace(".yaml", "");
}

function fileIssueCounts(validation: AuthoringValidation | null) {
  const counts: Record<string, { errors: number; warnings: number }> = {};
  if (!validation) {
    return counts;
  }
  for (const issue of validation.errors) {
    const file = issue.file || "world";
    counts[file] = counts[file] ?? { errors: 0, warnings: 0 };
    counts[file].errors += 1;
  }
  for (const issue of validation.warnings) {
    const file = issue.file || "world";
    counts[file] = counts[file] ?? { errors: 0, warnings: 0 };
    counts[file].warnings += 1;
  }
  return counts;
}

function groupValidationIssues(validation: AuthoringValidation) {
  const groups: Record<string, AuthoringValidation["errors"]> = {};
  for (const issue of [
    ...validation.errors,
    ...validation.warnings,
    ...validation.suggestions
  ]) {
    const file = issue.file || "world";
    groups[file] = [...(groups[file] ?? []), issue];
  }
  return groups;
}

function toErrorMessage(error: unknown): string {
  return getErrorMessageSafe(error);
}

function sanitizeDisplayError(message: string): string {
  return message
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/(authorization\s*[:=]\s*)(bearer\s+)?[A-Za-z0-9._~+/=-]+/gi, "[redacted authorization]")
    .replace(/((?:transient[_-]?)?api[_-]?key|secret[_-]?ref|provider[_-]?secret|relay[_-]?token|access[_-]?token|secret|token|password)\s*[:=]\s*['"]?[^'",\s}\]]+/gi, "$1=[redacted]")
    .replace(/([?&](?:api[_-]?key|key|token|access[_-]?token|secret|signature|sig|auth|authorization)=)[^&#\s"'<>]+/gi, "$1[redacted]")
    .replace(/(\/(?:token|tokens|key|keys|secret|secrets|bearer|auth)\/)[A-Za-z0-9._~+/=-]{8,}/gi, "$1[redacted]")
    .replace(/(raw[_\s-]?provider[_\s-]?(?:error|response)|provider[_\s-]?raw[_\s-]?response|raw[_\s-]?response)\s*[:=]\s*[^}\n]+/gi, "[redacted provider response]")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/\/[^\s"'<>]*(?:\.env|\.db|\.sqlite|logs?|cache|backups?|crash-reports|node_modules|dist)[^\s"'<>]*/gi, "[local path redacted]")
    .replace(/(hidden[_\s-]?facts?|npc[_\s-]?secrets?|raw[_\s-]?prompts?|state[_\s-]?deltas?)\s*[:=]\s*[^}\n]+/gi, "$1=[redacted]")
    .replace(/Traceback[\s\S]*/i, "[stack trace redacted]");
}

function redactAuthoringPreviewText(value: string): string {
  const sanitized = sanitizeDisplayError(value)
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/(authorization\s*[:=]\s*)(bearer\s+)?[A-Za-z0-9._~+/=-]+/gi, "[redacted authorization]")
    .replace(/((?:transient[_-]?)?api[_-]?key|provider[_-]?secret|secret[_-]?ref|relay[_-]?token|access[_-]?token|token|password)\s*[:=]\s*['"]?[^'",\s}\]]+/gi, "$1=[redacted]");
  const sensitiveLine = /(hidden|secret|private|npc[_-]?knowledge|witness|raw[_-]?state[_-]?delta|state[_-]?deltas|debug|api[_-]?key|authorization|provider[_-]?secret|mature_only|raw[_-]?prompt)/i;
  return sanitized
    .split(/\r?\n/)
    .map((line) => {
      if (!sensitiveLine.test(line)) {
        return line;
      }
      const keyed = line.match(/^(\s*[-]?\s*["']?[^:#\n"']+["']?\s*:\s*)(.*)$/);
      if (keyed) {
        return `${keyed[1]}[authoring-only redacted]`;
      }
      const listItem = line.match(/^(\s*-\s*)(.*)$/);
      if (listItem) {
        return `${listItem[1]}[authoring-only redacted]`;
      }
      return "[authoring-only redacted]";
    })
    .join("\n");
}

function authoringErrorMessage(error: unknown): string {
  const message = toErrorMessage(error);
  if (message.includes("[object Object]")) {
    return "Authoring request failed. Check validation errors from the backend.";
  }
  return message;
}
