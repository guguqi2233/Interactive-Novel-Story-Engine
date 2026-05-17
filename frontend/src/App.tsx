import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AuthoringValidation,
  AuthoringFilePreviewResponse,
  AuthoringModLoadOrderResponse,
  AuthoringModSummary,
  AuthoringModValidation,
  AuthoringWorldSummary,
  DebugEvent,
  DebugPerformanceRecentResponse,
  DebugPerformanceSummaryResponse,
  deleteSave,
  exportModArchive,
  exportSaveArchive,
  exportWorldArchive,
  applySaveMigration,
  dryRunSaveMigration,
  fetchAuthoringFile,
  fetchAuthoringFiles,
  fetchAuthoringMod,
  fetchAuthoringModLoadOrder,
  fetchAuthoringMods,
  fetchAuthoringWorld,
  fetchAuthoringWorlds,
  fetchScenarioTemplates,
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
  fetchPlaytest,
  fetchPlaytestRecent,
  fetchSaveDebugEvents,
  fetchSaveMigrationStatus,
  fetchSessionDebugEvents,
  fetchStudioConfigSummary,
  fetchStudioStatus,
  GameInputResponse,
  GraphResponse,
  listSaves,
  loadGame,
  NarrativeEvalReport,
  PlaytestReport,
  previewAuthoringFileChange,
  previewQuestGraph,
  previewScenarioTemplate,
  runNarrativeEval,
  runPlaytest,
  saveGame,
  saveAuthoringFile,
  SaveSummary,
  SaveMigrationResponse,
  SaveMigrationStatus,
  ScenarioTemplate,
  ScenarioTemplatePreviewResponse,
  QuestGraphResponse,
  QuestStageNode,
  startGame,
  StudioConfigSummary,
  StudioStatus,
  submitPlayerInput,
  validateAuthoringWorld,
  validateAuthoringMod,
  VisibleState
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
  "relationships.yaml"
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
  "relationships.yaml": "relationships"
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

export function App() {
  const [sessionId, setSessionId] = useState<string>("");
  const [selectedWorldId, setSelectedWorldId] = useState<string>("mist_valley");
  const [visibleState, setVisibleState] = useState<VisibleState | null>(null);
  const [turn, setTurn] = useState<number>(0);
  const [story, setStory] = useState<StoryEntry[]>([]);
  const [suggestedActions, setSuggestedActions] = useState<string[]>([]);
  const [input, setInput] = useState<string>("");
  const [debugOpen, setDebugOpen] = useState<boolean>(true);
  const [lastResponse, setLastResponse] = useState<unknown>(null);
  const [timeline, setTimeline] = useState<DebugEvent[]>([]);
  const [timelineError, setTimelineError] = useState<string>("");
  const [playerRelationshipGraph, setPlayerRelationshipGraph] = useState<GraphResponse | null>(null);
  const [playerFactionGraph, setPlayerFactionGraph] = useState<GraphResponse | null>(null);
  const [debugRelationshipGraph, setDebugRelationshipGraph] = useState<GraphResponse | null>(null);
  const [debugFactionGraph, setDebugFactionGraph] = useState<GraphResponse | null>(null);
  const [graphError, setGraphError] = useState<string>("");
  const [debugGraphError, setDebugGraphError] = useState<string>("");
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
  const [playtestError, setPlaytestError] = useState<string>("");

  useEffect(() => {
    void handleStart();
    void refreshSaves();
    void refreshStudioStatus();
    void refreshStudioConfigSummary();
    void refreshNarrativeEvals();
    void refreshPerformance();
    void refreshPlaytests();
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
      setSuggestedActions(["observe", "smithy", "wait"]);
      setStory([{ id: Date.now(), text: "A new local story session has started." }]);
      setLastResponse(response);
      void refreshTimeline(response.session_id);
      void refreshPlayerGraphs(response.session_id);
      void refreshDebugGraphs(response.session_id);
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

  async function handleSelectPlaytest(runId: string) {
    setPlaytestError("");
    try {
      const report = await fetchPlaytest(runId);
      setSelectedPlaytest(report);
    } catch (err) {
      setPlaytestError(toErrorMessage(err));
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
      const response = await submitPlayerInput(sessionId, trimmedInput);
      applyGameInputResponse(response);
      setInput("");
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
      setSuggestedActions(["observe", "smithy", "wait"]);
      setStory([{ id: Date.now(), text: `Loaded save ${response.save_id}.` }]);
      setLastResponse(response);
      void refreshTimeline(response.session_id);
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
    const confirmed = window.confirm(`Delete local save ${saveId}?`);
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
    const confirmed = window.confirm(
      "Apply migration to this save? The backend will migrate through the registered migration service."
    );
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
            error={studioStatusError}
            configError={studioConfigError}
            narrativeEvalError={narrativeEvalError}
            performanceError={performanceError}
            playtestError={playtestError}
            onRefresh={() => {
              void refreshStudioStatus();
              void refreshStudioConfigSummary();
              void refreshSaves();
              void refreshNarrativeEvals();
              void refreshPerformance();
              void refreshPlaytests();
            }}
            onRunNarrativeEval={() => void handleRunNarrativeEval()}
            onSelectNarrativeEval={(runId) => void handleSelectNarrativeEval(runId)}
            onRefreshPerformance={() => void refreshPerformance()}
            onRunPlaytest={(options) => void handleRunPlaytest(options)}
            onSelectPlaytest={(runId) => void handleSelectPlaytest(runId)}
            onRefreshPlaytests={() => void refreshPlaytests()}
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
            placeholder="Enter your action..."
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
            <button type="button" onClick={() => void refreshDebugGraphs()} disabled={!sessionId || isLoading}>
              Refresh Graphs
            </button>
            <button
              type="button"
              onClick={() => void refreshSaveTimeline()}
              disabled={!selectedSaveId || isLoading}
            >
              Load Save Timeline
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
  error,
  configError,
  narrativeEvalError,
  performanceError,
  playtestError,
  onRefresh,
  onRunNarrativeEval,
  onSelectNarrativeEval,
  onRefreshPerformance,
  onRunPlaytest,
  onSelectPlaytest,
  onRefreshPlaytests,
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
  error: string;
  configError: string;
  narrativeEvalError: string;
  performanceError: string;
  playtestError: string;
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
  onSelectPlaytest: (runId: string) => void;
  onRefreshPlaytests: () => void;
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
                  <span className="muted"> · {save.formatted_time}</span>
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
                ? ` · ${status.playtest_summary.latest_status}`
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
        error={playtestError}
        onRun={onRunPlaytest}
        onSelect={onSelectPlaytest}
        onRefresh={onRefreshPlaytests}
      />

      <SettingsPrivacyPanel summary={configSummary} error={configError} />

      <LocalOnlyNotice>
        Dashboard data is a safe local summary. It does not include API keys, raw GameState,
        raw state_deltas, or hidden narrative facts.
      </LocalOnlyNotice>
    </section>
  );
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
                {shortRunId(report.run_id)} · {report.passed}/{report.total_cases}
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
                  <span className="muted"> · {formatStageDurations(sample.stage_durations_ms)}</span>
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
  error,
  onRun,
  onSelect,
  onRefresh
}: {
  reports: PlaytestReport[];
  selectedReport: PlaytestReport | null;
  error: string;
  onRun: (options: {
    worldId: string;
    agentType: string;
    steps: number;
    seed: number;
    saveLoadCheck: boolean;
  }) => void;
  onSelect: (runId: string) => void;
  onRefresh: () => void;
}) {
  const [worldId, setWorldId] = useState<string>("mist_valley");
  const [agentType, setAgentType] = useState<string>("random_valid_action_agent");
  const [steps, setSteps] = useState<number>(12);
  const [seed, setSeed] = useState<number>(123);
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

function SettingsPrivacyPanel({
  summary,
  error
}: {
  summary: StudioConfigSummary | null;
  error: string;
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
            <DashboardCard title="Local APIs" value="Status">
              <StatusDot label="Authoring" enabled={summary.authoring_api_enabled} />
              <StatusDot label="Debug" enabled={summary.debug_api_enabled} />
              <StatusDot label="Performance" enabled={summary.performance_logging_enabled} />
              <StatusDot label="Playtest" enabled={summary.playtest_api_enabled} />
              <StatusDot label="Eval" enabled={summary.eval_api_enabled} />
            </DashboardCard>
          </div>
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

function AuthoringPanel() {
  const [worlds, setWorlds] = useState<AuthoringWorldSummary[]>([]);
  const [selectedWorldId, setSelectedWorldId] = useState<string>("");
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("manifest.yaml");
  const [content, setContent] = useState<string>("");
  const [diskContent, setDiskContent] = useState<string>("");
  const [viewMode, setViewMode] = useState<AuthoringViewMode>("raw");
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
      !window.confirm("Warnings or save-impact risks were found. Save this local file anyway?")
    ) {
      return;
    }
    const confirmed = window.confirm(
      "This saves a local content pack file on this machine. Continue?"
    );
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

        <button type="button" onClick={handleValidate} disabled={!selectedWorldId || isBusy}>
          Validate
        </button>
        <button type="button" onClick={() => void handlePreview()} disabled={!selectedWorldId || isBusy}>
          Preview
        </button>
        <button type="button" onClick={handleSave} disabled={!selectedWorldId || !selectedFile || isBusy}>
          Save
        </button>
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

      <div className="authoring-workspace">
        <WorldFileTree
          files={usableFiles}
          selectedFile={selectedFile}
          validation={validation}
          onSelectFile={(fileName) => {
            if (isDirty && !window.confirm("Discard unsaved local edits and switch files?")) {
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
              if (isDirty && issue.file !== selectedFile && !window.confirm("Discard unsaved local edits and switch files?")) {
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

      {selectedWorldId && selectedFile === "quests.yaml" && (
        <QuestGraphEditor
          worldId={selectedWorldId}
          onPreviewYaml={(yamlContent, validationResult) => {
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
      )}

      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
      {selectedIssuePath && (
        <p className="muted">
          Selected issue path: <code>{selectedIssuePath}</code>
        </p>
      )}
      <ScenarioTemplatePanel />
      <ModManagerPanel />
    </section>
  );
}

function ScenarioTemplatePanel() {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [preview, setPreview] = useState<ScenarioTemplatePreviewResponse | null>(null);
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

  useEffect(() => {
    void loadTemplates();
  }, []);

  const selectedTemplate =
    templates.find((template) => template.id === selectedTemplateId) ?? templates[0] ?? null;

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
      setTemplates(response.templates);
      setSelectedTemplateId((current) => current || response.templates[0]?.id || "");
    } catch (err) {
      setTemplates([]);
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
      const response = await previewScenarioTemplate(selectedTemplate.id, variables);
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

  const variableNames = selectedTemplate
    ? Array.from(new Set([...selectedTemplate.required_variables, ...Object.keys(selectedTemplate.optional_variables)]))
    : [];

  return (
    <section className="mod-manager-panel authoring-zone">
      <div className="authoring-pane-header">
        <div>
          <h2>Scenario Templates</h2>
          <p className="muted">Preview reusable local content drafts without writing files or changing active saves.</p>
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
            Template
            <select
              value={selectedTemplate?.id ?? ""}
              onChange={(event) => setSelectedTemplateId(event.target.value)}
              disabled={isBusy}
            >
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          <div>
            <p className="muted">{selectedTemplate?.description}</p>
            <span className="badge">{selectedTemplate?.template_type}</span>
          </div>
        </div>
      ) : (
        <EmptyState title="No templates available." detail="Add local templates under the templates directory." />
      )}

      {selectedTemplate && (
        <div className="template-variable-grid">
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
      )}

      <div className="authoring-header-actions">
        <button type="button" onClick={() => void handlePreviewTemplate()} disabled={!selectedTemplate || isBusy}>
          Preview Template
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
            <p className={preview.validation_report.ok ? "muted" : "error"}>
              Validation: {preview.validation_report.ok ? "passed" : `${preview.validation_report.errors.length} errors`}
            </p>
          )}
          <pre className="template-preview-code">
            {preview.rendered.files[0]?.content || "No rendered content."}
          </pre>
        </div>
      )}

      {message && <p className="muted">{message}</p>}
      <ErrorPanel message={error} />
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
  const [error, setError] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [isBusy, setIsBusy] = useState<boolean>(false);

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

  async function handleGraphPreview() {
    if (!graph) {
      return;
    }
    setIsBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await previewQuestGraph(worldId, graph);
      onPreviewYaml(response.yaml_content, response.validation);
      setMessage(response.validation.ok ? "Quest graph preview is valid." : "Quest graph preview has errors.");
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
            <h3>{selectedQuest?.title}</h3>
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
            </div>

            {selectedStage && (
              <div className="form-grid">
                <label>
                  Stage title
                  <input
                    value={selectedStage.title}
                    onChange={(event) => updateStage((stage) => ({ ...stage, title: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Stage description
                  <textarea
                    value={selectedStage.description}
                    onChange={(event) => updateStage((stage) => ({ ...stage, description: event.target.value }))}
                    disabled={isBusy}
                  />
                </label>
                <label>
                  Objectives
                  <textarea
                    value={selectedStage.objectives.map((objective) => objective.text).join("\n")}
                    onChange={(event) =>
                      updateStage((stage) => ({
                        ...stage,
                        objectives: event.target.value
                          .split("\n")
                          .map((line) => line.trim())
                          .filter(Boolean)
                          .map((text) => ({ id: text, text }))
                      }))
                    }
                    disabled={isBusy}
                  />
                </label>
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
                      {edge.source} {"->"} {edge.target} ({edge.type})
                    </span>
                  ))}
              />
            </section>

            <section className="studio-section">
              <h3>Triggers</h3>
              <ItemList
                emptyText="No triggers."
                items={(selectedQuest?.triggers ?? []).map((trigger) => (
                  <span key={`${trigger.type}-${trigger.id}-${trigger.action}`}>
                    {trigger.type}:{trigger.id} / {trigger.action}
                    {trigger.next_stage ? ` -> ${trigger.next_stage}` : ""}
                  </span>
                ))}
              />
            </section>

            <button type="button" onClick={() => void handleGraphPreview()} disabled={!graph || isBusy}>
              Convert Graph To YAML Preview
            </button>
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
