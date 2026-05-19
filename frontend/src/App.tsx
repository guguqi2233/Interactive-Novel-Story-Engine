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
  NPCBehaviorTimelineResponse,
  DebugPerformanceRecentResponse,
  DebugPerformanceSummaryResponse,
  applyScenarioTemplate,
  applyTemplateWizard,
  applyNPCSimulationPresetDraft,
  applyRPScenarioTemplate,
  deleteSave,
  dryRunNPCSimulationTick,
  dryRunSaveTimelineReplay,
  exportModArchive,
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
  fetchReferenceIndex,
  fetchLocalContentLibrary,
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
  fetchStudioStatus,
  fetchContentCoverage,
  reviewContentDiff,
  GameInputResponse,
  ContentDiffReview,
  GraphResponse,
  listSaves,
  loadGame,
  NarrativeEvalReport,
  PlaytestReport,
  PlaytestBatchRun,
  previewAuthoringFileChange,
  previewAuthoringMap,
  previewAuthoringScenario,
  previewQuestGraph,
  previewScenarioTemplate,
  previewTemplateWizard,
  previewWorldMerge,
  previewRPScenarioTemplate,
  runNarrativeEval,
  runContentCoverage,
  runPlaytest,
  runPlaytestBatch,
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
  MerchantEconomyNode,
  ShopInventoryEdge,
  CharacterCardImportReport,
  RumorAuthoringNode,
  RumorCrimeConsequenceAuthoring,
  RPCharacterAuthoring,
  RPCharacterAuthoringProfile,
  DialogueSceneAuthoring,
  DialogueSceneTemplate,
  GroupRPSceneAuthoring,
  GroupRPSceneTemplate,
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
  const [saves, setSaves] = useState<SaveSummary[]>([]);
  const [selectedSaveId, setSelectedSaveId] = useState<string>("");
  const [migrationStatusBySaveId, setMigrationStatusBySaveId] = useState<Record<string, SaveMigrationStatus>>({});
  const [migrationResultBySaveId, setMigrationResultBySaveId] = useState<Record<string, SaveMigrationResponse>>({});
  const [migrationError, setMigrationError] = useState<string>("");
  const [saveWorldFilter, setSaveWorldFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [mode, setMode] = useState<"studio" | "play" | "authoring">("studio");
  const [studioStatus, setStudioStatus] = useState<StudioStatus | null>(null);
  const [studioStatusError, setStudioStatusError] = useState<string>("");
  const [studioConfigSummary, setStudioConfigSummary] = useState<StudioConfigSummary | null>(null);
  const [studioConfigError, setStudioConfigError] = useState<string>("");
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
          <h2>Mode</h2>
          <div className="segmented">
            <button
              type="button"
              className={mode === "studio" ? "active" : ""}
              onClick={() => setMode("studio")}
            >
              Studio
            </button>
            <button
              type="button"
              className={mode === "play" ? "active" : ""}
              onClick={() => setMode("play")}
            >
              Play
            </button>
            <button
              type="button"
              className={mode === "authoring" ? "active" : ""}
              onClick={() => setMode("authoring")}
            >
              Authoring
            </button>
          </div>
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
        {mode === "authoring" ? (
          <AuthoringPanel />
        ) : mode === "studio" ? (
          <StudioHome
            status={studioStatus}
            configSummary={studioConfigSummary}
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
            configError={studioConfigError}
            narrativeEvalError={narrativeEvalError}
            performanceError={performanceError}
            playtestError={playtestError}
            scenarioRegressionError={scenarioRegressionError}
            worldHealthError={worldHealthError}
            contentCoverageError={contentCoverageError}
            onRefresh={() => {
              void refreshStudioStatus();
              void refreshStudioConfigSummary();
              void refreshSaves();
              void refreshNarrativeEvals();
              void refreshPerformance();
              void refreshPlaytests();
              void refreshWorldHealth();
              void refreshContentCoverage();
            }}
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
            onNavigate={setMode}
          />
        ) : (
          <>
        <div className="story-scroll">
          {story.map((entry) => (
            <article className="story-entry" key={entry.id}>
              {entry.text}
            </article>
          ))}
          {story.length === 0 && <EmptyState title="Creating a local game session..." detail="The player view only uses visible state returned by the backend." />}
        </div>

        {suggestedActions.length > 0 && (
          <div className="suggestions">
            {suggestedActions.map((action) => (
              <button type="button" key={action} onClick={() => setInput(action)}>
                {action}
              </button>
            ))}
          </div>
        )}

        <form className="input-row" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={dialogue?.dialogue_session.status === "active" ? "Say something in dialogue..." : "Enter your action..."}
            disabled={isLoading || !sessionId}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>

        <ErrorPanel message={error} />
          </>
        )}
      </section>

      <aside className={`debug-panel ${debugOpen ? "open" : "closed"}`}>
        <button className="debug-toggle" type="button" onClick={() => setDebugOpen(!debugOpen)}>
          {debugOpen ? "Hide Debug" : "Debug"}
        </button>

        {debugOpen && (
          <div className="debug-content">
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
            <section className="timeline">
              <h2>Timeline</h2>
              {timelineError && <p className="error">{timelineError}</p>}
              {timelineError && timelineError.toLowerCase().includes("debug") && (
                <p className="muted">debug disabled</p>
              )}
              {timeline.length === 0 && !timelineError && <p className="muted">No events yet.</p>}
              {timeline.map((event) => (
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
            </section>
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
            />
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
          </div>
        )}
      </aside>
    </main>
  );
}

function StudioHome({
  status,
  configSummary,
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
  configError,
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
  onSelectPromptProfile,
  onNavigate
}: {
  status: StudioStatus | null;
  configSummary: StudioConfigSummary | null;
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
  configError: string;
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
  onSelectPromptProfile: (profileId: string) => void;
  onNavigate: (mode: "studio" | "play" | "authoring") => void;
}) {
  const recentSaves = status?.recent_saves.length ? status.recent_saves : saves.slice(0, 5);
  const validationSummaries = status?.validation_summaries ?? [];
  const unhealthyWorlds = validationSummaries.filter((item) => !item.ok).length;

  return (
    <section className="studio-home">
      <PageHeader
        eyebrow="Local Studio"
        title="Project Dashboard"
        description="Safe status for local worlds, saves, validation, providers, and studio tools."
        actions={<button type="button" onClick={onRefresh}>Refresh</button>}
      />

      <ErrorPanel message={error} />

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
        onOpenAuthoring={() => onNavigate("authoring")}
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

      <SettingsPrivacyPanel summary={configSummary} error={configError} onSelectPromptProfile={onSelectPromptProfile} />

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
  onOpenAuthoring: () => void;
}) {
  const [showUncoveredOnly, setShowUncoveredOnly] = useState<boolean>(false);
  const rows = report ? contentCoverageRows(report) : [];
  const average = rows.length
    ? Math.round(rows.reduce((total, row) => total + row.summary.coverage_percent, 0) / rows.length)
    : 0;
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
          <button type="button" onClick={onOpenAuthoring}>Authoring</button>
        </div>
      </div>
      <ErrorPanel message={error} compact />
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
    </section>
  );
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
  return value.replace(/hidden_fact_text_visible:[^\s,;]+/g, "hidden_fact_text_visible:[redacted]");
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
  const entries = summary?.entries ?? [];
  const samples = recent?.samples ?? [];
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
          <h3>Performance</h3>
          <p className="muted">Local samples only. Prompt text, hidden facts, and API keys are not recorded.</p>
        </div>
        <button type="button" onClick={onRefresh}>
          Refresh Performance
        </button>
      </div>
      <ErrorPanel message={error} compact />
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
  const issueCount = selectedReport
    ? selectedReport.errors.length +
      selectedReport.invariant_violations.length +
      selectedReport.visibility_leaks.length +
      selectedReport.save_load_failures.length
    : 0;

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
          <SectionCard title="Actions" description="Recent agent inputs through GameLoop.">
            <ItemList
              emptyText="No actions."
              items={selectedReport.actions_taken.slice(-8).map((action) => (
                <span key={`${action.step}-${action.input_text}`}>
                  #{action.step} {action.input_text} <span className="badge">{action.result}</span>
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
        </div>
      ) : (
        <EmptyState title="No playtest selected." detail="Run a deterministic playtest to inspect actions and invariant checks." />
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
                    <pre>{JSON.stringify(result.expected_summary, null, 2)}</pre>
                  </div>
                  <div>
                    <strong>Actual</strong>
                    <pre>{JSON.stringify(result.actual_summary, null, 2)}</pre>
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

function SettingsPrivacyPanel({
  summary,
  error,
  onSelectPromptProfile
}: {
  summary: StudioConfigSummary | null;
  error: string;
  onSelectPromptProfile: (profileId: string) => void;
}) {
  return (
    <section className="studio-section privacy-panel">
      <div className="authoring-pane-header">
        <div>
          <h3>Settings / Local Privacy</h3>
          <p className="muted">Safe configuration summary without API keys, raw env, or full local paths.</p>
        </div>
        <StatusBadge label={summary?.local_only ? "Local only" : "Unavailable"} enabled={Boolean(summary?.local_only)} />
      </div>
      <ErrorPanel message={error} compact />
      {summary ? (
        <>
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
        selectedSave={selectedSave}
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
  selectedSave,
  status,
  result,
  error,
  isLoading,
  onCheck,
  onDryRun,
  onApply
}: {
  selectedSave: SaveSummary | null;
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
        <h3>Migration</h3>
        <EmptyState title="No save selected." detail="Select a save to inspect migration status." />
      </div>
    );
  }

  return (
    <div className="migration-panel">
      <h3>Migration</h3>
      <ErrorPanel message={error} compact />
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
        </div>
      )}
    </div>
  );
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
        <details>
          <summary>Preview output</summary>
          <pre>{previewContent}</pre>
        </details>
      )}
    </section>
  );
}

function confirmDangerousAction(message: string): boolean {
  return window.confirm(message);
}

type ImportPackageKind = "world" | "mod" | "save";

function ImportPackagePanel() {
  const [kind, setKind] = useState<ImportPackageKind>("world");
  const [archiveBase64, setArchiveBase64] = useState<string>("");
  const [overwrite, setOverwrite] = useState<boolean>(false);
  const [result, setResult] = useState<ArchiveImportResponse | null>(null);
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

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
          ? await importWorldArchive(archive, overwrite)
          : kind === "mod"
            ? await importModArchive(archive, overwrite)
            : await importSaveArchive(archive, overwrite);
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
          <input type="checkbox" checked={overwrite} onChange={(event) => setOverwrite(event.target.checked)} disabled={isBusy} />
          Allow overwrite
        </label>
      </div>
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

function AuthoringPanel() {
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
  const [safeExport, setSafeExport] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);
  const referenceIndex = useReferenceIndex(worldId);

  useEffect(() => {
    void loadCharacters();
  }, [worldId]);

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

            <AuthoringActionBar
              onPreview={() => void handlePreview()}
              onValidate={() => void handleValidate()}
              onSave={() => void handleSave()}
              disabled={isBusy}
            />
            <button type="button" onClick={() => void handleSafeExport()} disabled={isBusy || !selectedNpcId}>Export Safe Character Card</button>
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
          <pre>{previewYaml}</pre>
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
              <pre className="template-preview-code">{file.content}</pre>
            </details>
          ))}
        </div>
      )}
      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
    </section>
  );
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
          {Object.entries(draft.proposed_files).slice(0, 3).map(([fileName, content]) => <details key={fileName}><summary>{fileName}</summary><pre className="template-preview-code">{content}</pre></details>)}
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

const LIBRARY_TYPES: Array<"all" | LocalContentType> = ["all", "world", "character_pack", "template_pack", "scenario_suite", "prompt_profile", "RP_profile", "mod"];

function LocalContentLibraryPanel({ onOpenEditor }: { onOpenEditor: (toolId: AuthoringToolId) => void }) {
  const [items, setItems] = useState<LocalContentLibraryItem[]>([]);
  const [filter, setFilter] = useState<"all" | LocalContentType>("all");
  const [selectedId, setSelectedId] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
  const [archiveDraft, setArchiveDraft] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadItems();
  }, [filter]);

  async function loadItems() {
    setIsBusy(true);
    setError("");
    try {
      const response = await fetchLocalContentLibrary(filter);
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
      const response = await exportLocalContentLibraryItem(selected.content_type, selected.id);
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
      const response = await importLocalContentLibraryArchive(archiveDraft.trim(), false, confirmApply);
      setMessage(JSON.stringify(response));
      void loadItems();
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
          <h2>Local Content Library</h2>
          <p className="muted">Worlds, character packs, templates, scenario suites, prompt/RP profiles, and mods.</p>
        </div>
        <button type="button" onClick={() => void loadItems()} disabled={isBusy}>Refresh Library</button>
      </div>
      <div className="template-grid">
        <label>Type<select value={filter} onChange={(event) => setFilter(event.target.value as "all" | LocalContentType)}>{LIBRARY_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}</select></label>
        <label>Item<select value={selected?.id ?? ""} onChange={(event) => setSelectedId(event.target.value)}>{items.map((item) => <option key={`${item.content_type}:${item.id}`} value={item.id}>{item.name}</option>)}</select></label>
      </div>
      {selected ? (
        <div className="diff-summary">
          <h3>{selected.name}</h3>
          <p>{selected.content_type} / {selected.id}</p>
          <p className="muted">{selected.description || "No description."}</p>
          <p>Path: {selected.path_label}</p>
          <pre className="template-preview-code">{JSON.stringify(selected.metadata, null, 2)}</pre>
          <div className="authoring-header-actions">
            <button type="button" onClick={() => void handleValidate()} disabled={isBusy || !selected.capabilities.includes("validate")}>Validate</button>
            <button type="button" onClick={() => void handleExport()} disabled={isBusy || !selected.capabilities.includes("export")}>Export</button>
            <button type="button" onClick={() => onOpenEditor(libraryToolForItem(selected))}>Open Editor</button>
          </div>
        </div>
      ) : <EmptyState title="No content items." detail="The local library did not find matching items." />}
      {validation && <ValidationPanel validation={validation} onSelectIssue={() => undefined} />}
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
          <pre className="template-preview-code">
            {preview.rendered.files[0]?.content || "No rendered content."}
          </pre>
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
                      {issue.path}: {issue.message}
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
                <pre className="authoring-preview-box">{scenarioDraftJson}</pre>
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
                      {issue.path}: {issue.message}
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
          <pre>{JSON.stringify(selectedEntity.fields, null, 2)}</pre>
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
                <li key={note}>{note}</li>
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
                <strong>{issue.path}</strong>
                <span>{issue.code}</span>
                <span>{issue.message}</span>
                {issue.ref_id && <span>ref: {issue.ref_id}</span>}
                {issue.suggestion && <span>fix: {issue.suggestion}</span>}
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
  dryRunError
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
}) {
  const filteredTurns = useMemo(() => filterTimelineTurns(timeline, selectedFilter), [timeline, selectedFilter]);
  const replaySummary = dryRun?.replay_summary ?? timeline?.replay_summary ?? null;
  const eventCount = filteredTurns.reduce((total, turnGroup) => total + turnGroup.events.length, 0);
  const deltaCount = filteredTurns.reduce(
    (total, turnGroup) =>
      total + turnGroup.events.reduce((turnTotal, event) => turnTotal + event.delta_count, 0),
    0
  );

  return (
    <section className="debug-group timeline-replay">
      <h2>Timeline Replay</h2>
      <div className="timeline-controls">
        <label>
          Source
          <select value={source} disabled>
            <option value="session">Session</option>
            <option value="save">Save</option>
          </select>
        </label>
        <label>
          Filter
          <select value={selectedFilter} onChange={(event) => onFilterChange(event.target.value as TimelineFilter)}>
            {TIMELINE_FILTERS.map((filter) => (
              <option key={filter} value={filter}>
                {filter}
              </option>
            ))}
          </select>
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
          </div>
          {replaySummary && <ReplaySummaryView summary={replaySummary} />}
          {filteredTurns.length === 0 ? (
            <EmptyState title="No timeline events." detail="Try another filter or load a session/save replay." />
          ) : (
            <div className="timeline-turns">
              {filteredTurns.map((turnGroup) => (
                <section className="timeline-turn" key={turnGroup.turn}>
                  <h3>
                    Turn {turnGroup.turn}
                    <span>{turnGroup.events.length} events</span>
                    <span>{turnGroup.events.reduce((total, event) => total + event.delta_count, 0)} deltas</span>
                  </h3>
                  {turnGroup.events.map((event) => (
                    <TimelineEventCard event={event} key={event.event_id} />
                  ))}
                </section>
              ))}
            </div>
          )}
        </>
      ) : (
        !error && <EmptyState title="No replay loaded." detail="Load a debug session or save replay." />
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

function TimelineEventCard({ event }: { event: TimelineEventView }) {
  const deltaSummary = event.state_deltas
    .slice(0, 3)
    .map((delta) => `${delta.operation} ${delta.path}`)
    .join("; ");
  return (
    <details className={`timeline-event replay-event ${event.event_kind}`}>
      <summary>
        <span>#{event.event_id}</span>
        <span>{event.event_kind}</span>
        <span>{event.action_type}</span>
        <span>{event.actor_id}</span>
        <span>{event.result}</span>
      </summary>
      <dl className="event-details">
        <dt>Visible</dt>
        <dd>{event.visible_to_player ? "yes" : "no"}</dd>
        <dt>Target</dt>
        <dd>{event.target_id ?? "None"}</dd>
        <dt>Created</dt>
        <dd>{event.created_at}</dd>
        <dt>Delta summary</dt>
        <dd>{deltaSummary || "No deltas"}</dd>
      </dl>
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
      <details>
        <summary>StateDelta details ({event.state_deltas.length})</summary>
        <pre>{JSON.stringify(event.state_deltas, null, 2)}</pre>
      </details>
    </details>
  );
}

function filterTimelineTurns(
  timeline: TimelineReplayResponse | null,
  filter: TimelineFilter
): TimelineReplayResponse["turns"] {
  if (!timeline) {
    return [];
  }
  if (filter === "all") {
    return timeline.turns;
  }
  return timeline.turns
    .map((turnGroup) => ({
      ...turnGroup,
      events: turnGroup.events.filter((event) => timelineEventMatchesFilter(event, filter))
    }))
    .filter((turnGroup) => turnGroup.events.length > 0);
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
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed.";
}

function sanitizeDisplayError(message: string): string {
  return message
    .replace(/sk-[A-Za-z0-9_-]+/g, "sk-[redacted]")
    .replace(/[A-Z]:\\[^\s"'<>]+/g, "[local path redacted]")
    .replace(/\/[^\s"'<>]*(?:\.env|\.db|logs?)[^\s"'<>]*/gi, "[local path redacted]");
}

function authoringErrorMessage(error: unknown): string {
  const message = toErrorMessage(error);
  if (message.includes("[object Object]")) {
    return "Authoring request failed. Check validation errors from the backend.";
  }
  return message;
}
