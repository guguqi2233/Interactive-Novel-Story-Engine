import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
import {
  AuthoringValidation,
  AuthoringFilePreviewResponse,
  AuthoringWorldSummary,
  DebugEvent,
  deleteSave,
  fetchAuthoringFile,
  fetchAuthoringFiles,
  fetchAuthoringWorld,
  fetchAuthoringWorlds,
  fetchGameState,
  fetchDebugFactionGraph,
  fetchDebugRelationshipGraph,
  fetchPlayerFactionGraph,
  fetchPlayerRelationshipGraph,
  fetchSaveDebugEvents,
  fetchSessionDebugEvents,
  GameInputResponse,
  GraphResponse,
  listSaves,
  loadGame,
  previewAuthoringFileChange,
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
      void refreshPlayerGraphs(response.session_id);
      void refreshDebugGraphs(response.session_id);
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
          <h2>Graphs</h2>
          {graphError && <p className="error compact-error">{graphError}</p>}
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
      <header className="authoring-header">
        <div>
          <h1>World Authoring</h1>
          <p className="muted">Local structured editor backed by the authoring API and validator.</p>
        </div>
        <div className="authoring-header-actions">
          {isDirty && <span className="dirty-badge">Unsaved changes</span>}
          <button type="button" onClick={() => void loadWorlds()} disabled={isBusy}>
            Refresh Worlds
          </button>
        </div>
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

      {message && <p className="muted">{message}</p>}
      {error && <p className="error">{error}</p>}
      {selectedIssuePath && (
        <p className="muted">
          Selected issue path: <code>{selectedIssuePath}</code>
        </p>
      )}
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
    return <p className="muted">No validation result yet.</p>;
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
      {Object.keys(groupedIssues).length === 0 && <p className="muted">No issues.</p>}
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

function authoringErrorMessage(error: unknown): string {
  const message = toErrorMessage(error);
  if (message.includes("[object Object]")) {
    return "Authoring request failed. Check validation errors from the backend.";
  }
  return message;
}
