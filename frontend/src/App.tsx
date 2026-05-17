import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AuthoringValidation,
  AuthoringWorldSummary,
  DebugEvent,
  deleteSave,
  fetchAuthoringFile,
  fetchAuthoringFiles,
  fetchAuthoringWorld,
  fetchAuthoringWorlds,
  fetchGameState,
  fetchSaveDebugEvents,
  fetchSessionDebugEvents,
  GameInputResponse,
  listSaves,
  loadGame,
  saveGame,
  saveAuthoringFile,
  SaveSummary,
  startGame,
  submitPlayerInput,
  validateAuthoringWorld,
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
  const [saves, setSaves] = useState<SaveSummary[]>([]);
  const [selectedSaveId, setSelectedSaveId] = useState<string>("");
  const [saveWorldFilter, setSaveWorldFilter] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [mode, setMode] = useState<"play" | "authoring">("play");

  useEffect(() => {
    void handleStart();
    void refreshSaves();
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
    } catch (err) {
      setError(toErrorMessage(err));
    } finally {
      setIsLoading(false);
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

  async function refreshSaves(nextSelectedSaveId?: string, worldFilter = saveWorldFilter) {
    const response = await listSaves(worldFilter || undefined);
    setSaves(response.saves);
    setSelectedSaveId(nextSelectedSaveId ?? response.saves[0]?.save_id ?? "");
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
          saveWorldFilter={saveWorldFilter}
          isLoading={isLoading}
          onSave={handleSave}
          onLoad={handleLoad}
          onDelete={(saveId) => void handleDeleteSave(saveId)}
          onRefresh={() => void refreshSaves(selectedSaveId)}
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
          <h2>Status</h2>
          <StatusPanel visibleState={visibleState} />
        </section>
          </>
        )}
      </aside>

      <section className="story-panel">
        {mode === "authoring" ? (
          <AuthoringPanel />
        ) : (
          <>
        <div className="story-scroll">
          {story.map((entry) => (
            <article className="story-entry" key={entry.id}>
              {entry.text}
            </article>
          ))}
          {story.length === 0 && <p className="muted">Creating a local game session...</p>}
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

        {error && <p className="error">{error}</p>}
          </>
        )}
      </section>

      <aside className={`debug-panel ${debugOpen ? "open" : "closed"}`}>
        <button className="debug-toggle" type="button" onClick={() => setDebugOpen(!debugOpen)}>
          {debugOpen ? "Hide Debug" : "Debug"}
        </button>

        {debugOpen && (
          <div className="debug-content">
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
  saveWorldFilter,
  isLoading,
  onSave,
  onLoad,
  onDelete,
  onRefresh,
  onSelectSave,
  onFilterWorld
}: {
  saves: SaveSummary[];
  selectedSaveId: string;
  saveWorldFilter: string;
  isLoading: boolean;
  onSave: () => void;
  onLoad: () => void;
  onDelete: (saveId: string) => void;
  onRefresh: () => void;
  onSelectSave: (saveId: string) => void;
  onFilterWorld: (worldId: string) => void;
}) {
  const worldOptions = Array.from(new Set(saves.map((save) => save.world_id))).sort();
  return (
    <section>
      <h2>Save Browser</h2>
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
      </div>
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
        {saves.length === 0 && <p className="muted">No saves.</p>}
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
    </section>
  );
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
            ? `${visibleState.active_combat.id} (${visibleState.active_combat.status})`
            : "None"}
        </p>
      </div>
    </div>
  );
}

function AuthoringPanel() {
  const [worlds, setWorlds] = useState<AuthoringWorldSummary[]>([]);
  const [selectedWorldId, setSelectedWorldId] = useState<string>("");
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>("manifest.yaml");
  const [content, setContent] = useState<string>("");
  const [validation, setValidation] = useState<AuthoringValidation | null>(null);
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
    } catch (err) {
      setContent("");
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

  async function handleSave() {
    if (!selectedWorldId || !selectedFile) {
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
      setMessage("Saved and validated.");
    } catch (err) {
      setError(authoringErrorMessage(err));
    } finally {
      setIsBusy(false);
    }
  }

  const usableFiles = files.length > 0 ? files : AUTHORING_FILES;
  const disabled = isBusy || worlds.length === 0;

  return (
    <section className="authoring-panel">
      <header className="authoring-header">
        <div>
          <h1>World Authoring</h1>
          <p className="muted">Local YAML editor backed by the authoring API and validator.</p>
        </div>
        <button type="button" onClick={() => void loadWorlds()} disabled={isBusy}>
          Refresh
        </button>
      </header>

      {error.toLowerCase().includes("authoring api is disabled") && (
        <div className="notice">
          Authoring API is disabled. Set <code>ENABLE_AUTHORING_API=true</code> on the backend to
          use the local editor.
        </div>
      )}

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

        <label>
          File
          <select
            value={selectedFile}
            onChange={(event) => setSelectedFile(event.target.value)}
            disabled={disabled}
          >
            {usableFiles.map((fileName) => (
              <option key={fileName} value={fileName}>
                {fileName}
              </option>
            ))}
          </select>
        </label>

        <button type="button" onClick={handleValidate} disabled={!selectedWorldId || isBusy}>
          Validate
        </button>
        <button type="button" onClick={handleSave} disabled={!selectedWorldId || !selectedFile || isBusy}>
          Save
        </button>
      </div>

      <textarea
        className="yaml-editor"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        spellCheck={false}
        disabled={disabled}
      />

      {message && <p className="muted">{message}</p>}
      {error && <p className="error">{error}</p>}
      {selectedIssuePath && (
        <p className="muted">
          Selected issue path: <code>{selectedIssuePath}</code>
        </p>
      )}
      <ValidationPanel
        validation={validation}
        onSelectIssue={(issue) => {
          setSelectedIssuePath(issue.path);
          if (issue.file && usableFiles.includes(issue.file)) {
            setSelectedFile(issue.file);
          }
        }}
      />
    </section>
  );
}

function ValidationPanel({
  validation,
  onSelectIssue
}: {
  validation: AuthoringValidation | null;
  onSelectIssue: (issue: AuthoringValidation["errors"][number]) => void;
}) {
  if (!validation) {
    return <p className="muted">No validation result yet.</p>;
  }
  const groupedIssues = groupValidationIssues(validation);
  return (
    <section className="validation-panel">
      <h2>Validation</h2>
      <p className={validation.ok ? "validation-ok" : "error"}>
        {validation.ok ? "Loadable" : "Errors must be fixed before loading."}
      </p>
      {Object.entries(groupedIssues).map(([file, issues]) => (
        <div className="validation-file-group" key={file}>
          <h3>{file}</h3>
          <ValidationIssueList issues={issues} onSelectIssue={onSelectIssue} />
        </div>
      ))}
      {Object.keys(groupedIssues).length === 0 && <p className="muted">No issues.</p>}
    </section>
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

function authoringErrorMessage(error: unknown): string {
  const message = toErrorMessage(error);
  if (message.includes("[object Object]")) {
    return "Authoring request failed. Check validation errors from the backend.";
  }
  return message;
}
