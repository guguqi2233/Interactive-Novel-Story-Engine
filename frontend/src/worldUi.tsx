import { FormEvent, ReactNode } from "react";
import {
  DebugEvent,
  SaveMigrationStatus,
  SaveSummary,
  StudioConfigSummary,
  TimelineEventView,
  VisibleNPC,
  VisibleObject,
  VisibleQuest,
  VisibleState
} from "./api";

export type WorldActionCategory =
  | "all"
  | "core"
  | "movement"
  | "social"
  | "inventory"
  | "stealth"
  | "combat"
  | "module"
  | "other";

const WORLD_ACTION_FILTERS: { id: WorldActionCategory; label: string }[] = [
  { id: "all", label: "All" },
  { id: "core", label: "Core" },
  { id: "movement", label: "Movement" },
  { id: "social", label: "Social" },
  { id: "inventory", label: "Inventory" },
  { id: "stealth", label: "Stealth" },
  { id: "combat", label: "Combat" },
  { id: "module", label: "Module" },
  { id: "other", label: "Other" }
];

export function WorldWorkspaceShell({
  title = "World Studio UI Pro",
  visibleState,
  sessionId,
  debugEnabled,
  providerSummary,
  left,
  main,
  right,
  bottom
}: {
  title?: string;
  visibleState: VisibleState | null;
  sessionId: string;
  debugEnabled: boolean;
  providerSummary?: string;
  left: ReactNode;
  main: ReactNode;
  right: ReactNode;
  bottom?: ReactNode;
}) {
  return (
    <div className="world-workspace-shell">
      <header className="world-toolbar">
        <div>
          <p className="eyebrow">World Studio UI Pro</p>
          <h2>{title}</h2>
          <p className="muted">
            Normal World UI uses visible_state only. No hidden facts, NPC secrets, raw state_deltas,
            API key, raw env, or provider secret is shown.
          </p>
        </div>
        <WorldToolbar
          sessionId={sessionId}
          turn={visibleState?.turn ?? 0}
          location={visibleState?.location.name ?? "No active session"}
          debugEnabled={debugEnabled}
          providerSummary={providerSummary}
        />
      </header>
      <div className="world-workspace-grid">
        <nav className="world-workspace-nav" aria-label="World workspace navigation">
          {left}
        </nav>
        <section className="world-workspace-main">{main}</section>
        <aside className="world-workspace-context">{right}</aside>
      </div>
      <footer className="world-workspace-status">
        {bottom ?? (
          <>
            <span>Local-only</span>
            <span>World Engine is the fact source</span>
            <span>{debugEnabled ? "Debug gated: enabled" : "Debug gated: disabled"}</span>
          </>
        )}
      </footer>
    </div>
  );
}

export function WorldToolbar({
  sessionId,
  turn,
  location,
  debugEnabled,
  providerSummary
}: {
  sessionId: string;
  turn: number;
  location: string;
  debugEnabled: boolean;
  providerSummary?: string;
}) {
  return (
    <div className="world-toolbar-status" aria-label="World local status">
      <span className="badge">{sessionId ? "Session active" : "No session"}</span>
      <span className="badge">Turn {turn}</span>
      <span className="badge">{location}</span>
      <span className="badge">{providerSummary ?? "Provider Gateway only"}</span>
      <span className="badge">{debugEnabled ? "ENABLE_DEBUG_API on" : "ENABLE_DEBUG_API off"}</span>
    </div>
  );
}

export function WorldPlayMainView({ children }: { children: ReactNode }) {
  return <section id="world-play" className="world-play-main-view">{children}</section>;
}

export function WorldStudioNavigation({ onJump }: { onJump?: (targetId: string) => void }) {
  const entries = [
    ["world-play", "Story"],
    ["world-map", "Map"],
    ["world-npcs", "NPCs"],
    ["world-quests", "Quests"],
    ["world-inventory", "Inventory"],
    ["world-modules", "Modules"],
    ["world-timeline", "Timeline"],
    ["world-saves", "Saves"],
    ["world-quality", "Quality"],
    ["world-debug", "Debug"]
  ];
  return (
    <section className="world-nav-panel" aria-label="World Studio sections">
      <h3>World Navigation</h3>
      <p className="muted">Local play workspace. UI calls backend APIs and never directly modifies GameState.</p>
      <div className="chip-list vertical">
        {entries.map(([targetId, label]) => (
          <button type="button" className="chip-button" key={targetId} onClick={() => onJump?.(targetId)}>
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}

export function WorldWorkspaceNavigation({
  visibleState,
  debugEnabled,
  onJump
}: {
  visibleState: VisibleState | null;
  debugEnabled: boolean;
  onJump?: (targetId: string) => void;
}) {
  const entries = [
    { id: "world-play", label: "Story", value: visibleState ? `Turn ${visibleState.turn}` : "No session" },
    { id: "world-map", label: "Map", value: visibleState?.location.name ?? "Start session" },
    { id: "world-npcs", label: "NPCs", value: String(visibleState?.visible_npcs.length ?? 0) },
    { id: "world-quests", label: "Quests", value: String(visibleState?.quests.length ?? 0) },
    { id: "world-inventory", label: "Inventory", value: String(visibleState?.inventory.length ?? 0) },
    { id: "world-modules", label: "Modules", value: visibleState?.active_combat ? "Combat active" : "Safe summaries" },
    { id: "world-timeline", label: "Timeline", value: "Visible events" },
    { id: "world-saves", label: "Saves", value: "Local slots" },
    { id: "world-quality", label: "Quality", value: "Local checks" },
    { id: "world-debug", label: "Debug", value: debugEnabled ? "Gated on" : "Gated off" }
  ];
  return (
    <section className="world-nav-panel" aria-label="World Studio Pro navigation">
      <h3>World Workspace</h3>
      <p className="muted">Daily local play workspace. Actions call backend APIs and never directly modify GameState.</p>
      <div className="world-nav-link-list">
        {entries.map((entry) => (
          <button type="button" className="world-nav-link" key={entry.id} onClick={() => onJump?.(entry.id)}>
            <span>{entry.label}</span>
            <small>{entry.value}</small>
          </button>
        ))}
      </div>
      <p className="muted">No account. No cloud sync. No online play. No online marketplace.</p>
    </section>
  );
}

export function WorldStatusCard({ title, value, detail }: { title: string; value: string; detail?: string }) {
  return (
    <section className="safe-summary-card world-status-card">
      <p className="muted">{title}</p>
      <strong>{value}</strong>
      {detail && <p>{detail}</p>}
    </section>
  );
}

export function LocationCard({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const exits = Object.entries(visibleState?.location.exits ?? {});
  return (
    <VisibleStateSection id="world-map" title="Map / Location Panel" empty={!visibleState} emptyDetail="Start a session to inspect known locations.">
      <LocationSummary locationName={visibleState?.location.name ?? "Unknown"} locationId={visibleState?.location.id ?? "none"} />
      <div className="chip-list">
        {exits.length ? exits.map(([direction, target]) => (
          <button type="button" className="chip-button" key={`${direction}-${target}`} onClick={() => onAction?.(`move ${direction}`)}>
            {direction} {"->"} {target}
          </button>
        )) : <span className="muted">No visible exits.</span>}
      </div>
      <p className="muted">Unknown locations, hidden exits, hidden objects, and debug location info are excluded. No online play is introduced.</p>
    </VisibleStateSection>
  );
}

export const MapLocationPanel = LocationCard;

function LocationSummary({ locationName, locationId }: { locationName: string; locationId: string }) {
  return (
    <dl className="metadata-list">
      <dt>Current location</dt>
      <dd>{locationName}</dd>
      <dt>Location ref</dt>
      <dd>{locationId}</dd>
    </dl>
  );
}

export function NPCSafeCard({ npc, onAction }: { npc: VisibleNPC; onAction?: (action: string) => void }) {
  return (
    <article className="world-mini-card">
      <strong>{npc.id}</strong>
      <p className="muted">Mood {npc.mood}; relationship band {relationshipBand(npc.relationship_to_player)}</p>
      {npc.condition && <span className="badge">{npc.condition}</span>}
      <button type="button" onClick={() => onAction?.(`talk ${npc.id}`)}>Talk</button>
    </article>
  );
}

export function NPCRelationshipPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const npcs = visibleState?.visible_npcs ?? [];
  const relationships = visibleState?.relationships ?? [];
  return (
    <VisibleStateSection id="world-npcs" title="NPC / Relationship Panel" empty={!visibleState} emptyDetail="Start a session to inspect visible NPCs.">
      <div className="world-card-list">
        {npcs.length ? npcs.map((npc) => <NPCSafeCard key={npc.id} npc={npc} onAction={onAction} />) : <p className="muted">No visible NPCs.</p>}
      </div>
      <h4>Known relationships</h4>
      {relationships.length ? (
        <ul className="compact-list">
          {relationships.map((relationship) => (
            <li key={relationship.id}>
              {relationship.source_id} {relationship.relation_type} {relationship.target_id}
              <span className="badge">trust {relationshipBand(relationship.trust)}</span>
            </li>
          ))}
        </ul>
      ) : <p className="muted">No known relationship summaries.</p>}
      <p className="muted">NPC secrets, NPC hidden knowledge, hidden relationships, and debug memory are not displayed.</p>
    </VisibleStateSection>
  );
}

export function QuestCard({ quest }: { quest: VisibleQuest }) {
  const objectives = quest.objectives ?? [];
  return (
    <article className="world-mini-card">
      <strong>{quest.title ?? quest.name}</strong>
      <p className="muted">{quest.description ?? quest.stage_description ?? "Known quest summary only."}</p>
      <span className="badge">{quest.status}</span>
      {quest.stage_title && <span className="badge">{quest.stage_title}</span>}
      {objectives.length > 0 && (
        <ul className="compact-list">
          {objectives.map((objective) => (
            <li key={objective.id}>
              {objective.id} {objective.completed ? "(done)" : "(open)"}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export function QuestJournalPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const quests = visibleState?.quests ?? [];
  return (
    <VisibleStateSection id="world-quests" title="Quest / Journal Panel" empty={!visibleState} emptyDetail="Start a session to inspect known quests.">
      <div className="world-card-list">
        {quests.length ? quests.map((quest) => <QuestCard key={quest.id} quest={quest} />) : <p className="muted">No known quests.</p>}
      </div>
      <p className="muted">Hidden objectives, hidden truth, and debug quest state are excluded from normal view.</p>
    </VisibleStateSection>
  );
}

export function InventoryItemCard({ item, onAction }: { item: VisibleObject; onAction?: (action: string) => void }) {
  return (
    <article className="world-mini-card">
      <strong>{item.id}</strong>
      <p className="muted">Visible item summary only. Hidden item properties and debug economy data are excluded.</p>
      <button type="button" onClick={() => onAction?.(`use_item ${item.id}`)}>Use item</button>
    </article>
  );
}

export function InventoryTradePanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const inventory = visibleState?.inventory ?? [];
  const visibleObjects = visibleState?.visible_objects ?? [];
  return (
    <VisibleStateSection id="world-inventory" title="Inventory / Trade UI" empty={!visibleState} emptyDetail="Start a session to inspect visible inventory.">
      <div className="world-card-list">
        {inventory.length ? inventory.map((item) => <InventoryItemCard key={item.id} item={item} onAction={onAction} />) : <p className="muted">Inventory empty.</p>}
      </div>
      <WorldStatusCard title="Visible containers / objects" value={String(visibleObjects.length)} detail={visibleObjects.map((item) => item.id).join(", ") || "No visible trade container."} />
      <WorldStatusCard title="Trade" value="Backend validated" detail="No authoritative prices are calculated in the frontend." />
    </VisibleStateSection>
  );
}

export function SuggestedActionCard({
  action,
  onSelect,
  disabled = false
}: {
  action: string;
  onSelect: (action: string) => void;
  disabled?: boolean;
}) {
  const category = categorizeWorldAction(action);
  return (
    <button type="button" className="suggested-action-card" onClick={() => onSelect(action)} disabled={disabled}>
      <strong>{actionLabel(action)}</strong>
      <span className="badge">{category}</span>
      <span className="muted">Target: {actionTarget(action)}</span>
      <span className="muted">Time: backend validated</span>
      <span className="muted">Requirements: safe summary only; hidden requirements are not shown.</span>
    </button>
  );
}

export function WorldActionInputPanel({
  input,
  suggestedActions,
  recentActions,
  category,
  isLoading,
  hasSession,
  placeholder,
  onInputChange,
  onCategoryChange,
  onSelectAction,
  onSubmit
}: {
  input: string;
  suggestedActions: string[];
  recentActions: string[];
  category: WorldActionCategory;
  isLoading: boolean;
  hasSession: boolean;
  placeholder: string;
  onInputChange: (value: string) => void;
  onCategoryChange: (category: WorldActionCategory) => void;
  onSelectAction: (action: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const filteredActions = suggestedActions.filter((action) => category === "all" || categorizeWorldAction(action) === category);
  return (
    <section className="world-action-input-panel">
      <header className="panel-header">
        <div>
          <h3>World Action Input / Suggested Actions UX</h3>
          <p className="muted">Actions submit through /game/input. The UI does not apply StateDelta or decide success/failure.</p>
        </div>
        <label>
          Category
          <select value={category} onChange={(event) => onCategoryChange(event.target.value as WorldActionCategory)}>
            {WORLD_ACTION_FILTERS.map((filter) => <option key={filter.id} value={filter.id}>{filter.label}</option>)}
          </select>
        </label>
      </header>
      <div className="suggested-action-grid">
        {filteredActions.length ? filteredActions.map((action) => (
          <SuggestedActionCard key={action} action={action} onSelect={onSelectAction} disabled={!hasSession || isLoading} />
        )) : <p className="muted">No suggested actions for this category.</p>}
      </div>
      {recentActions.length > 0 && (
        <div>
          <h4>Recent actions</h4>
          <div className="chip-list">
            {recentActions.map((action) => (
              <button type="button" className="chip-button" key={action} onClick={() => onSelectAction(action)} disabled={!hasSession || isLoading}>
                {action}
              </button>
            ))}
          </div>
        </div>
      )}
      <form className="input-row" onSubmit={onSubmit}>
        <input
          value={input}
          onChange={(event) => onInputChange(event.target.value)}
          placeholder={placeholder}
          disabled={isLoading || !hasSession}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Send
        </button>
      </form>
    </section>
  );
}

export function ModuleStatusBadge({ label, enabled }: { label: string; enabled: boolean }) {
  return <span className={`status-badge ${enabled ? "enabled" : "disabled"}`}>{label}: {enabled ? "available" : "unavailable"}</span>;
}

export function VisibleStateSection({
  id,
  title,
  children,
  empty,
  emptyDetail
}: {
  id?: string;
  title: string;
  children: ReactNode;
  empty?: boolean;
  emptyDetail?: string;
}) {
  return (
    <section id={id} className="section-card player">
      <div className="section-card-header">
        <div>
          <h3>{title}</h3>
          <p className="muted">Normal view is based on visible_state safe summaries.</p>
        </div>
      </div>
      {empty ? <div className="empty-state"><strong>No active visible state.</strong><p>{emptyDetail}</p></div> : children}
    </section>
  );
}

export function VisibleStateInspector({ visibleState }: { visibleState: VisibleState | null }) {
  return (
    <VisibleStateSection id="world-visible-state" title="Visible State Inspector" empty={!visibleState} emptyDetail="Start or load a session to inspect player-visible state.">
      <div className="safe-summary-grid">
        <WorldStatusCard title="Player" value={visibleState?.player_condition?.condition ?? "healthy"} />
        <WorldStatusCard title="Location" value={visibleState?.location.name ?? "Unknown"} />
        <WorldStatusCard title="Visible NPCs" value={String(visibleState?.visible_npcs.length ?? 0)} />
        <WorldStatusCard title="Inventory" value={String(visibleState?.inventory.length ?? 0)} />
        <WorldStatusCard title="Quests" value={String(visibleState?.quests.length ?? 0)} />
        <WorldStatusCard title="Known facts" value={String(visibleState?.known_facts.length ?? 0)} />
      </div>
      <p className="muted">This is not raw GameState. Hidden facts, NPC secrets, raw state_deltas, and debug memory are excluded.</p>
    </VisibleStateSection>
  );
}

export function EventSafeSummaryCard({ event }: { event: DebugEvent | TimelineEventView }) {
  return (
    <article className="world-mini-card">
      <strong>Turn {event.turn}</strong>
      <p>{event.action_type} by {event.actor_id}</p>
      <span className="badge">{event.result}</span>
      <p className="muted">Safe event summary. Raw state_deltas are debug-gated.</p>
    </article>
  );
}

export function WorldTimelineEventLogPanel({ events, debugEnabled }: { events: DebugEvent[]; debugEnabled: boolean }) {
  const visibleEvents = events.filter((event) => event.visible_to_player);
  return (
    <VisibleStateSection id="world-timeline" title="World Timeline / EventLog UI Pro" empty={false}>
      <div className="world-card-list">
        {visibleEvents.length ? visibleEvents.map((event) => <EventSafeSummaryCard key={event.event_id} event={event} />) : <p className="muted">No player-visible events loaded.</p>}
      </div>
      <p className="muted">Hidden events are excluded from normal view. Raw state_deltas require DebugGate and ENABLE_DEBUG_API.</p>
      <ModuleStatusBadge label="Debug timeline" enabled={debugEnabled} />
    </VisibleStateSection>
  );
}

export function SaveSlotCard({
  save,
  selected,
  migrationStatus,
  onSelect
}: {
  save: SaveSummary;
  selected: boolean;
  migrationStatus?: SaveMigrationStatus;
  onSelect: (saveId: string) => void;
}) {
  return (
    <button
      type="button"
      className={`save-card ${selected ? "selected" : ""}`}
      onClick={() => onSelect(save.save_id)}
    >
      <strong>{save.world_name || save.world_id}</strong>
      <span>{save.current_location_name}</span>
      <span>{save.formatted_time}</span>
      <span>Turn {save.turn}</span>
      <span>Schema {migrationStatus?.schema_version ?? "check pending"}</span>
      <span className="muted">{save.updated_at}</span>
    </button>
  );
}

export function WorldSaveLoadPanel({
  saves,
  selectedSaveId,
  migrationStatusBySaveId,
  onSelectSave,
  onSaveCurrent,
  onLoadSelected,
  onDeleteSelected,
  onRefresh,
  hasSession = false,
  busy = false
}: {
  saves: SaveSummary[];
  selectedSaveId: string;
  migrationStatusBySaveId: Record<string, SaveMigrationStatus>;
  onSelectSave: (saveId: string) => void;
  onSaveCurrent?: () => void;
  onLoadSelected?: () => void;
  onDeleteSelected?: () => void;
  onRefresh?: () => void;
  hasSession?: boolean;
  busy?: boolean;
}) {
  return (
    <VisibleStateSection id="world-saves" title="World Save / Load UX Pro" empty={false}>
      <div className="button-row">
        <button type="button" onClick={onSaveCurrent} disabled={!hasSession || busy}>Create save</button>
        <button type="button" onClick={onLoadSelected} disabled={!selectedSaveId || busy}>Load selected</button>
        <button type="button" onClick={onDeleteSelected} disabled={!selectedSaveId || busy}>Delete selected</button>
        <button type="button" onClick={onRefresh} disabled={busy}>Refresh saves</button>
      </div>
      <div className="save-list">
        {saves.length ? saves.map((save) => (
          <SaveSlotCard
            key={save.save_id}
            save={save}
            selected={selectedSaveId === save.save_id}
            migrationStatus={migrationStatusBySaveId[save.save_id]}
            onSelect={onSelectSave}
          />
        )) : <p className="muted">No saves yet.</p>}
      </div>
      <p className="muted">Save summaries exclude raw GameState, hidden facts, API keys, and raw state_deltas. Load and delete operations stay behind backend flows and confirmation where destructive.</p>
    </VisibleStateSection>
  );
}

export function TacticalCombatPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const combat = visibleState?.active_combat;
  const actions = ["tactical_move", "take_cover", "aim", "strike", "defend", "guard", "flee_tactical"];
  return (
    <VisibleStateSection id="world-tactical" title="Tactical Combat UI Pro" empty={!visibleState} emptyDetail="Start a session to inspect combat state.">
      {combat ? (
        <>
          <WorldStatusCard title="Encounter" value={`${combat.combat_id} (${combat.status})`} detail={`Location ${combat.location_id}`} />
          <WorldStatusCard title="Player stance" value={combat.player_stance} detail={combat.player_condition} />
          <WorldStatusCard title="Player effects" value={combat.player_status_effects.join(", ") || "none"} detail="Hit and damage rolls stay backend/debug-gated." />
          <div className="chip-list">
            {combat.visible_combatants.map((combatant) => <span className="badge" key={combatant}>{combatant}</span>)}
          </div>
          <div className="suggested-action-grid">
            {actions.map((action) => <SuggestedActionCard key={action} action={action} onSelect={(value) => onAction?.(value)} />)}
          </div>
        </>
      ) : <p className="muted">No active encounter.</p>}
      <p className="muted">Hidden combatants and debug rolls are excluded. Combat results are backend-authoritative.</p>
    </VisibleStateSection>
  );
}

export function EconomyDashboardPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const rumors = visibleState?.known_rumors ?? [];
  const factions = visibleState?.factions ?? [];
  return (
    <VisibleStateSection id="world-economy" title="Economy Dashboard UI" empty={!visibleState} emptyDetail="Start a session to inspect known market hints.">
      <WorldStatusCard title="Known market hints" value={String(rumors.filter((rumor) => rumor.tags.some((tag) => /market|trade|price|scarcity/i.test(tag))).length)} detail="Derived from player-known rumors only." />
      <WorldStatusCard title="Known factions / merchants" value={String(factions.length)} detail={factions.map((faction) => `${faction.name}: ${faction.band}`).join(", ") || "No known market actor."} />
      <p className="muted">Hidden market info and debug economy data are excluded.</p>
    </VisibleStateSection>
  );
}

export function FactionWarDashboardPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const conflicts = visibleState?.faction_conflicts ?? [];
  return (
    <VisibleStateSection id="world-factions" title="Faction War Dashboard UI" empty={!visibleState} emptyDetail="Start a session to inspect known faction conflicts.">
      {conflicts.length ? (
        <ul className="compact-list">
          {conflicts.map((conflict) => (
            <li key={conflict.faction_id}>
              {conflict.faction_id}: alert {conflict.alert_level}, conflict {conflict.conflict_level}
            </li>
          ))}
        </ul>
      ) : <p className="muted">No known contested regions.</p>}
      <p className="muted">Hidden war regions and raw faction_war state are excluded.</p>
    </VisibleStateSection>
  );
}

export function DeductionBoardPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const facts = visibleState?.known_facts ?? [];
  const rumors = visibleState?.known_rumors ?? [];
  const crimes = visibleState?.known_crimes ?? [];
  return (
    <VisibleStateSection id="world-deduction" title="Deduction Board UI" empty={!visibleState} emptyDetail="Start a session to inspect known evidence.">
      <div className="safe-summary-grid">
        <WorldStatusCard title="Known evidence / facts" value={String(facts.length)} />
        <WorldStatusCard title="Known claims / rumors" value={String(rumors.length)} />
        <WorldStatusCard title="Known crimes" value={String(crimes.length)} />
      </div>
      {facts.length ? (
        <ul className="compact-list">
          {facts.map((fact) => <li key={fact.id}>{fact.id} <span className="muted">{fact.tags.join(", ")}</span></li>)}
        </ul>
      ) : <p className="muted">No known evidence or claims.</p>}
      <div className="chip-list">
        <button type="button" className="chip-button" onClick={() => onAction?.("form_hypothesis")}>form_hypothesis</button>
        <button type="button" className="chip-button" onClick={() => onAction?.("test_hypothesis")}>test_hypothesis</button>
      </div>
      <p className="muted">Hidden evidence, hidden truth, and debug solution are excluded.</p>
    </VisibleStateSection>
  );
}

export function SurvivalTravelPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const exits = Object.keys(visibleState?.location.exits ?? {});
  return (
    <VisibleStateSection id="world-survival" title="Survival / Travel UI" empty={!visibleState} emptyDetail="Start a session to inspect travel options.">
      <WorldStatusCard title="Survival status" value={visibleState?.player_condition?.condition ?? "safe summary unavailable"} detail="Fatigue, hunger, thirst, and route risk are shown only when safe summaries exist." />
      <WorldStatusCard title="Known routes" value={String(exits.length)} detail={exits.join(", ") || "No visible routes."} />
      <div className="chip-list">
        {exits.map((exit) => <button className="chip-button" type="button" key={exit} onClick={() => onAction?.(`travel_route ${exit}`)}>{exit}</button>)}
        {["make_camp", "forage", "rest_travel"].map((action) => <button className="chip-button" type="button" key={action} onClick={() => onAction?.(action)}>{action}</button>)}
      </div>
      <p className="muted">Hidden route danger and debug survival state are excluded.</p>
    </VisibleStateSection>
  );
}

export function WorldAdvancedModulePanels({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const groups = [
    { title: "Magic Panel", actions: ["cast_spell", "prepare_spell", "rest_focus"] },
    { title: "Hacking Panel", actions: ["scan_terminal", "hack_terminal", "extract_logs"] },
    { title: "Crafting Panel", actions: ["craft_item"] },
    { title: "Cultivation Panel", actions: ["meditate", "practice", "breakthrough", "consume_pill"] }
  ];
  return (
    <VisibleStateSection id="world-modules" title="Magic / Hacking / Crafting / Cultivation Module UI" empty={!visibleState} emptyDetail="Start a session to inspect enabled module actions.">
      <div className="safe-summary-grid">
        {groups.map((group) => (
          <section className="world-mini-card" key={group.title}>
            <strong>{group.title}</strong>
            <p className="muted">Safe summary only; hidden module knowledge is excluded.</p>
            <div className="chip-list">
              {group.actions.map((action) => <button type="button" className="chip-button" key={action} onClick={() => onAction?.(action)}>{action}</button>)}
            </div>
          </section>
        ))}
      </div>
    </VisibleStateSection>
  );
}

export function WorldPromptProviderPanel({
  configSummary,
  onOpenProviderSetup
}: {
  configSummary: StudioConfigSummary | null;
  onOpenProviderSetup: () => void;
}) {
  const selectedPrompt = configSummary?.prompt_profiles.find((profile) => profile.id === configSummary.selected_prompt_profile_id) ?? null;
  const providerStatus = configSummary?.provider_status ?? configSummary?.llm_provider ?? "safe summary unavailable";
  const useCases = ["intent_parser", "narrator", "memory_summary", "quality_eval"];
  return (
    <VisibleStateSection title="World Prompt / Provider UX Polish">
      <div className="safe-summary-grid">
        {useCases.map((useCase) => (
          <WorldStatusCard
            key={useCase}
            title={useCase}
            value={selectedPrompt?.name ?? "Default safe prompt profile"}
            detail={`${providerStatus}; model id shown only through safe provider summaries.`}
          />
        ))}
      </div>
      <p className="muted">Raw prompt hidden by default. Hidden facts, raw state_deltas, API key, raw env, and provider secret are excluded.</p>
      <button type="button" onClick={onOpenProviderSetup}>Open Provider Setup Wizard</button>
    </VisibleStateSection>
  );
}

export function WorldQualityPlaytestPanel({
  worldHealthStatus,
  playtestCount,
  onRunWorldHealth,
  onRunPlaytest,
  onOpenQuality
}: {
  worldHealthStatus: string;
  playtestCount: number;
  onRunWorldHealth: () => void;
  onRunPlaytest?: () => void;
  onOpenQuality: () => void;
}) {
  return (
    <VisibleStateSection id="world-quality" title="World Quality / Playtest UI">
      <div className="safe-summary-grid">
        <WorldStatusCard title="World quality" value={worldHealthStatus} detail="Safe report rows only." />
        <WorldStatusCard title="Recent playtests" value={String(playtestCount)} detail="No real provider calls are launched by this panel." />
      </div>
      <div className="chip-list">
        <button type="button" className="chip-button" onClick={onRunWorldHealth}>Run world quality gate</button>
        <button type="button" className="chip-button" onClick={onRunPlaytest} disabled={!onRunPlaytest}>Run default playtest</button>
        <button type="button" className="chip-button" onClick={onOpenQuality}>Open Quality Dashboard</button>
      </div>
      <p className="muted">Hidden text, raw state_deltas, and API key are not shown. Reports are local-only and not uploaded.</p>
    </VisibleStateSection>
  );
}

export function DebugGate({
  debugEnabled,
  title = "World Debug Boundary / Safe Debug UI",
  children
}: {
  debugEnabled: boolean;
  title?: string;
  children: ReactNode;
}) {
  if (!debugEnabled) {
    return <DebugDisabledState title={title} />;
  }
  return (
    <section className="debug-gate">
      <DebugWarningBanner title={title} />
      {children}
    </section>
  );
}

export function DebugDisabledState({ title }: { title: string }) {
  return (
    <div className="disabled-state debug-disabled-state">
      <strong>{title}</strong>
      <p>ENABLE_DEBUG_API required. Debug UI is disabled and normal UI remains player-facing safe.</p>
      <p className="muted">Debug data may include internal state and is never for player-facing view.</p>
    </div>
  );
}

export function DebugWarningBanner({ title }: { title: string }) {
  return (
    <div className="debug-warning-banner">
      <strong>{title}</strong>
      <p>ENABLE_DEBUG_API required. Debug data may include internal state, raw EventLog details, raw StateDelta, debug timeline, and module debug summaries.</p>
      <p>Never for player-facing view. Debug data is local-only and is not uploaded.</p>
    </div>
  );
}

function relationshipBand(value: number): string {
  if (value >= 70) return "high";
  if (value >= 30) return "warm";
  if (value <= -50) return "hostile";
  if (value <= -10) return "tense";
  return "neutral";
}

export function categorizeWorldAction(action: string): Exclude<WorldActionCategory, "all"> {
  const normalized = action.toLowerCase();
  if (/^(observe|wait|search)\b/.test(normalized)) return "core";
  if (/^(move|travel|travel_route|go)\b/.test(normalized)) return "movement";
  if (/^(talk|ask|dialogue|start_dialogue)\b/.test(normalized)) return "social";
  if (/^(use_item|use|trade|buy|sell|craft_item)\b/.test(normalized)) return "inventory";
  if (/^(sneak|lockpick|hide|shadow|distract)\b/.test(normalized)) return "stealth";
  if (/^(attack|strike|defend|guard|aim|take_cover|tactical|flee_tactical)\b/.test(normalized)) return "combat";
  if (/^(cast_spell|prepare_spell|rest_focus|scan_terminal|hack_terminal|extract_logs|meditate|practice|breakthrough|consume_pill|make_camp|forage|rest_travel|form_hypothesis|test_hypothesis)\b/.test(normalized)) return "module";
  return "other";
}

function actionLabel(action: string): string {
  return action.trim() || "Action";
}

function actionTarget(action: string): string {
  const parts = action.trim().split(/\s+/);
  return parts.length > 1 ? parts.slice(1).join(" ") : "current context";
}
