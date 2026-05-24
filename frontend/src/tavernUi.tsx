import { ReactNode, useEffect, useMemo, useState } from "react";
import {
  MultiNPCSceneSummary,
  RPSafetyDashboardReport,
  TavernCharacter,
  TavernMessage,
  TavernPreferences,
  TavernScenePreset,
  TavernSession,
  TavernSessionExportPreview,
  TavernSessionRecoveryRecord,
  WorldNpcSafeSummary
} from "./api";
import { buildSafeSearchIndex, safeSearchMatches, useDebouncedValue } from "./filterUtils";

function safeExcerpt(text?: string | null, max = 180): string {
  const value = (text ?? "").replace(
    /(api[_\s-]?key|authorization|hidden[_\s-]?fact|npc[_\s-]?secret|mature[_\s-]?memory|private[_\s-]?persona|raw[_\s-]?prompt|state[_\s-]?delta)\s*[:=]\s*[^\n,;]+/gi,
    "$1=[redacted]"
  );
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

export function SpeakerBadge({ speaker, speakerId }: { speaker?: string | null; speakerId?: string | null }) {
  return <span className={`speaker-badge speaker-${speaker || "unknown"}`}>{speaker || "speaker"}{speakerId ? ` · ${speakerId}` : ""}</span>;
}

export function RPSafetyBadge({ status = "safe" }: { status?: string }) {
  return <span className={`rp-safety-badge rp-safety-${status}`}>{status}</span>;
}

export function RelationshipToneBadge({ label = "tone safe summary" }: { label?: string }) {
  return <span className="relationship-tone-badge">{safeExcerpt(label, 80)}</span>;
}

export function EmotionStateBadge({ label = "emotion safe summary" }: { label?: string }) {
  return <span className="emotion-state-badge">{safeExcerpt(label, 80)}</span>;
}

export function SceneMoodBadge({ preset }: { preset?: TavernScenePreset | null }) {
  return <span className="scene-mood-badge">{preset ? `${preset.name} · ${(preset.mood_tags ?? []).join(", ") || "style only"}` : "no scene mood"}</span>;
}

export function TavernCharacterCard({ character, selected, onSelect }: { character: TavernCharacter; selected?: boolean; onSelect?: () => void }) {
  const tags = [
    character.linked_character_profile_id ? "CharacterProfile" : "profile missing",
    character.linked_world_npc_id ? `World NPC:${character.linked_world_npc_id}` : "no World NPC",
    character.rp_profile_id ? "RPProfile ready" : "RPProfile missing",
    character.voice_profile_id ? "VoiceProfile ready" : "VoiceProfile missing",
    ...(character.safety_flags ?? [])
  ];
  return (
    <button type="button" className={`tavern-card tavern-character-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <strong>{safeExcerpt(character.display_name, 80)}</strong>
      <p className="muted">{safeExcerpt(character.description) || "Project-local Tavern character draft."}</p>
      <div className="tavern-card-meta">
        <span>{character.linked_world_npc_id ? `world ref ${character.linked_world_npc_id}` : "no world ref"}</span>
        <span>{character.rp_profile_id ? "RP ok" : "RP draft"}</span>
        <span>{character.voice_profile_id ? "Voice ok" : "Voice draft"}</span>
        <RPSafetyBadge status={(character.safety_flags ?? []).length ? "review" : "safe"} />
      </div>
      <div className="tavern-chip-row">{tags.map((tag) => <span key={tag} className="tavern-chip">{safeExcerpt(tag, 50)}</span>)}</div>
    </button>
  );
}

export function TavernSessionCard({ session, selected, onSelect }: { session: TavernSession; selected?: boolean; onSelect?: () => void }) {
  return (
    <button type="button" className={`tavern-card tavern-session-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <strong>{safeExcerpt(session.title, 100)}</strong>
      <div className="tavern-card-meta">
        <span>{session.status}</span>
        <span>{session.message_count ?? 0} messages</span>
        <span>{session.character_ids.length} characters</span>
      </div>
    </button>
  );
}

export function TavernSessionListPro({
  sessions,
  selectedSessionId,
  onSelect
}: {
  sessions: TavernSession[];
  selectedSessionId?: string;
  onSelect?: (session: TavernSession) => void;
}) {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 180);
  const [statusFilter, setStatusFilter] = useState("all");
  const [pageSize, setPageSize] = useState(25);
  const [pageIndex, setPageIndex] = useState(0);
  const statusOptions = useMemo(() => ["all", ...Array.from(new Set(sessions.map((session) => session.status || "draft"))).sort()], [sessions]);
  const sessionSearchIndexById = useMemo(
    () =>
      new Map(
        sessions.map((session) => [
          session.session_id,
          buildSafeSearchIndex([
            session.session_id,
            session.title,
            session.status,
            session.character_ids.join(" "),
            String(session.message_count ?? 0)
          ])
        ])
      ),
    [sessions]
  );
  const filteredSessions = useMemo(
    () =>
      sessions.filter((session) => {
        if (statusFilter !== "all" && (session.status || "draft") !== statusFilter) return false;
        return !debouncedQuery || safeSearchMatches(sessionSearchIndexById.get(session.session_id) ?? "", debouncedQuery);
      }),
    [debouncedQuery, sessionSearchIndexById, sessions, statusFilter]
  );
  const pageCount = Math.max(1, Math.ceil(filteredSessions.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, filteredSessions.length);
  const visibleSessions = filteredSessions.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [debouncedQuery, pageSize, sessions.length, statusFilter]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  return (
    <div className="stack" data-windowed-tavern-sessions="true">
      <div className="tavern-filter-row">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search sessions, characters, safe metadata" />
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
        </select>
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[10, 25, 50].map((size) => <option key={size} value={size}>{size} rows</option>)}
        </select>
        {query !== debouncedQuery ? <span className="tavern-chip">filtering...</span> : null}
      </div>
      {sessions.length === 0 ? <p className="muted">No Tavern sessions yet.</p> : filteredSessions.length === 0 ? <p className="muted">No sessions match this safe filter.</p> : (
        <>
          <p className="muted">Rendering {windowStart + 1}-{windowEnd} of {filteredSessions.length} session(s).</p>
          {visibleSessions.map((session) => (
            <TavernSessionCard
              key={session.session_id}
              session={session}
              selected={session.session_id === selectedSessionId}
              onSelect={() => onSelect?.(session)}
            />
          ))}
          {filteredSessions.length > pageSize ? (
            <div className="pagination-controls" aria-label="Tavern session pagination">
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>First</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>Previous</button>
              <span>Page {clampedPageIndex + 1} / {pageCount}</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>Next</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>Last</button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export function RPMessageBubble({ message }: { message: TavernMessage }) {
  return (
    <article className="rp-message-bubble">
      <div className="rp-message-header">
        <SpeakerBadge speaker={message.speaker_type} speakerId={message.speaker_id} />
        <span className="muted">{message.created_at}</span>
      </div>
      <p>{safeExcerpt(message.content, 520)}</p>
      {message.safety_notes?.length ? (
        <details>
          <summary>Safety notes</summary>
          <ul>{message.safety_notes.map((note) => <li key={note}>{safeExcerpt(note)}</li>)}</ul>
        </details>
      ) : null}
    </article>
  );
}

export function TavernMessageListPro({ messages }: { messages: TavernMessage[] }) {
  const [messageSearch, setMessageSearch] = useState("");
  const debouncedMessageSearch = useDebouncedValue(messageSearch, 180);
  const [pageSize, setPageSize] = useState(50);
  const [pageIndex, setPageIndex] = useState(0);
  const messageSearchIndexById = useMemo(
    () =>
      new Map(
        messages.map((message) => [
          message.message_id,
          buildSafeSearchIndex([
            message.message_id,
            message.speaker_type,
            message.speaker_id,
            message.created_at,
            safeExcerpt(message.content, 520),
            ...(message.safety_notes ?? []).map((note) => safeExcerpt(note, 180))
          ])
        ])
      ),
    [messages]
  );
  const filteredMessages = useMemo(
    () =>
      messages.filter((message) => !debouncedMessageSearch || safeSearchMatches(messageSearchIndexById.get(message.message_id) ?? "", debouncedMessageSearch)),
    [debouncedMessageSearch, messageSearchIndexById, messages]
  );
  const pageCount = Math.max(1, Math.ceil(filteredMessages.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, filteredMessages.length);
  const visibleMessages = filteredMessages.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [debouncedMessageSearch, messages.length, pageSize]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  return (
    <div className="stack" data-windowed-tavern-message-list="true">
      <div className="tavern-filter-row">
        <input value={messageSearch} onChange={(event) => setMessageSearch(event.target.value)} placeholder="Search safe message metadata" />
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[25, 50, 100].map((size) => <option key={size} value={size}>{size} rows</option>)}
        </select>
        <button type="button" onClick={() => setPageIndex(Math.max(0, pageCount - 1))} disabled={filteredMessages.length === 0}>Jump to latest</button>
        {messageSearch !== debouncedMessageSearch ? <span className="tavern-chip">filtering...</span> : null}
      </div>
      {messages.length === 0 ? <p className="muted">No messages</p> : filteredMessages.length === 0 ? <p className="muted">No messages match this safe search.</p> : (
        <>
          <p className="muted">Rendering {windowStart + 1}-{windowEnd} of {filteredMessages.length} safe message(s).</p>
          {visibleMessages.map((message) => <RPMessageBubble key={message.message_id} message={message} />)}
          {filteredMessages.length > pageSize ? (
            <div className="pagination-controls" aria-label="Tavern message list pagination">
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>First</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>Previous</button>
              <span>Page {clampedPageIndex + 1} / {pageCount}</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>Next</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>Last</button>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}

export function MemorySummaryCard({ title, detail }: { title: string; detail?: string }) {
  return (
    <div className="memory-summary-card">
      <strong>{safeExcerpt(title, 120)}</strong>
      <p className="muted">{safeExcerpt(detail) || "Safe RP memory summary. Mature/private and debug memory stay hidden by default."}</p>
    </div>
  );
}

export function TavernSafeSummaryPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <aside className="tavern-safe-summary-panel">
      <h4>{title}</h4>
      {children}
      <p className="muted">Normal Tavern UI excludes API keys, hidden facts, NPC secrets, mature memory, private persona, raw prompts, and raw state_deltas.</p>
    </aside>
  );
}

export function TavernToolbar({ title, actions, meta }: { title: string; actions?: ReactNode; meta?: ReactNode }) {
  return (
    <div className="tavern-toolbar">
      <div>
        <h4>{title}</h4>
        {meta}
      </div>
      <div className="button-row">{actions}</div>
    </div>
  );
}

export function ChatSaveStatus({ dirty, saving, message }: { dirty?: boolean; saving?: boolean; message?: string }) {
  return <span className={`chat-save-status ${dirty ? "dirty" : "clean"}`}>{saving ? "saving..." : dirty ? "unsaved message draft" : message || "saved locally"}</span>;
}

export function TavernWorkspaceShell({ navigation, main, context, status }: { navigation: ReactNode; main: ReactNode; context: ReactNode; status: ReactNode }) {
  return (
    <section className="tavern-workspace-shell">
      <nav className="tavern-workspace-nav">{navigation}</nav>
      <main className="tavern-workspace-main">{main}</main>
      <aside className="tavern-workspace-context">{context}</aside>
      <footer className="tavern-workspace-status">{status}</footer>
    </section>
  );
}

export function CharacterCardLibrary({ characters, selectedCharacterId, onSelect }: { characters: TavernCharacter[]; selectedCharacterId?: string; onSelect?: (id: string) => void }) {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebouncedValue(query, 180);
  const [filter, setFilter] = useState("all");
  const characterSearchIndexById = useMemo(
    () =>
      new Map(
        characters.map((character) => [
          character.tavern_character_id,
          buildSafeSearchIndex([
            character.tavern_character_id,
            character.display_name,
            character.description,
            character.linked_character_profile_id,
            character.linked_world_npc_id,
            character.rp_profile_id,
            character.voice_profile_id,
            ...(character.safety_flags ?? [])
          ])
        ])
      ),
    [characters]
  );
  const filtered = useMemo(
    () =>
      characters.filter((character) => {
        const matchesQuery = !debouncedQuery || safeSearchMatches(characterSearchIndexById.get(character.tavern_character_id) ?? "", debouncedQuery);
        const matchesFilter =
          filter === "all" ||
          (filter === "linked_world" && Boolean(character.linked_world_npc_id)) ||
          (filter === "needs_profile" && (!character.rp_profile_id || !character.voice_profile_id)) ||
          (filter === "safety_review" && Boolean(character.safety_flags?.length));
        return matchesQuery && matchesFilter;
      }),
    [characterSearchIndexById, characters, debouncedQuery, filter]
  );
  return (
    <TavernSafeSummaryPanel title="Character Card Library">
      <div className="tavern-filter-row">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search characters, tags, linked refs" />
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="all">All characters</option>
          <option value="linked_world">Linked World NPC</option>
          <option value="needs_profile">Needs RP/Voice profile</option>
          <option value="safety_review">Safety review</option>
        </select>
        {query !== debouncedQuery ? <span className="tavern-chip">filtering...</span> : null}
      </div>
      {characters.length === 0 ? <p className="muted">No character cards yet. Import or create a local TavernCharacter draft.</p> : null}
      {filtered.length === 0 ? <p className="muted">No characters match this filter.</p> : (
        <div className="tavern-card-grid">
          {filtered.map((character) => (
            <TavernCharacterCard
              key={character.tavern_character_id}
              character={character}
              selected={character.tavern_character_id === selectedCharacterId}
              onSelect={() => onSelect?.(character.tavern_character_id)}
            />
          ))}
        </div>
      )}
      <p className="muted">Character card scripts are never executed and remote character downloads are not offered.</p>
    </TavernSafeSummaryPanel>
  );
}

export function TavernCharacterEditor({ character }: { character?: TavernCharacter | null }) {
  return (
    <TavernSafeSummaryPanel title="Tavern Character Editor / RP / Voice Profile Editor">
      {character ? (
        <div className="tavern-editor-grid">
          <label>Display name<input readOnly value={safeExcerpt(character.display_name, 120)} /></label>
          <label>Public description<textarea readOnly rows={3} value={safeExcerpt(character.description, 360)} /></label>
          <label>RPProfile status<input readOnly value={character.rp_profile_id ? `linked:${character.rp_profile_id}` : "draft needed"} /></label>
          <label>VoiceProfile status<input readOnly value={character.voice_profile_id ? `linked:${character.voice_profile_id}` : "draft needed"} /></label>
          <label>Boundary refs<input readOnly value={(character.safety_flags ?? []).join(", ") || "project defaults"} /></label>
          <details>
            <summary>Private persona / authoring notes (authoring-only, collapsed)</summary>
            <p className="muted">Private persona and creator notes are not shown in normal RP preview, prompt preview, export, or player-safe adapters.</p>
          </details>
        </div>
      ) : <p className="muted">Select a character to review public fields, RP profile, Voice profile, example dialogue, and boundary refs.</p>}
    </TavernSafeSummaryPanel>
  );
}

export function SingleCharacterChatPro({
  session,
  character,
  messages,
  input,
  providerStatus,
  memoryHints,
  safetyNotes,
  onInputChange,
  onSend,
  onRecoveryDraft
}: {
  session?: TavernSession | null;
  character?: TavernCharacter | null;
  messages: TavernMessage[];
  input: string;
  providerStatus?: string;
  memoryHints?: string[];
  safetyNotes?: string[];
  onInputChange?: (value: string) => void;
  onSend?: () => void;
  onRecoveryDraft?: () => void;
}) {
  const [showSafety, setShowSafety] = useState(false);
  const [messageSearch, setMessageSearch] = useState("");
  const debouncedMessageSearch = useDebouncedValue(messageSearch, 180);
  const [messagePageSize, setMessagePageSize] = useState(50);
  const [messagePageIndex, setMessagePageIndex] = useState(0);
  const messageSearchIndexById = useMemo(
    () =>
      new Map(
        messages.map((message) => [
          message.message_id,
          buildSafeSearchIndex([
            message.message_id,
            message.speaker_type,
            message.speaker_id,
            message.created_at,
            safeExcerpt(message.content, 520),
            ...(message.safety_notes ?? []).map((note) => safeExcerpt(note, 180))
          ])
        ])
      ),
    [messages]
  );
  const filteredMessages = useMemo(
    () =>
      messages.filter((message) => !debouncedMessageSearch || safeSearchMatches(messageSearchIndexById.get(message.message_id) ?? "", debouncedMessageSearch)),
    [debouncedMessageSearch, messageSearchIndexById, messages]
  );
  const messagePageCount = Math.max(1, Math.ceil(filteredMessages.length / messagePageSize));
  const clampedMessagePageIndex = Math.min(messagePageIndex, messagePageCount - 1);
  const messageWindowStart = clampedMessagePageIndex * messagePageSize;
  const messageWindowEnd = Math.min(messageWindowStart + messagePageSize, filteredMessages.length);
  const visibleMessages = filteredMessages.slice(messageWindowStart, messageWindowEnd);

  useEffect(() => {
    setMessagePageIndex(0);
  }, [debouncedMessageSearch, messagePageSize, messages.length]);

  useEffect(() => {
    if (messagePageIndex > messagePageCount - 1) {
      setMessagePageIndex(messagePageCount - 1);
    }
  }, [messagePageCount, messagePageIndex]);

  function jumpToLatestMessage() {
    setMessagePageIndex(Math.max(0, messagePageCount - 1));
  }

  return (
    <div className="single-character-chat-pro">
      <TavernToolbar
        title="Single Character Chat Pro"
        meta={<p className="muted">{session?.title ?? "No session selected"} · active character {character?.display_name ?? "none"} · provider {providerStatus ?? "Provider Gateway safe route"}</p>}
        actions={<ChatSaveStatus dirty={Boolean(input.trim())} message="saved locally" />}
      />
      <div className="tavern-chat-side-row">
        <button type="button" onClick={() => setShowSafety((value) => !value)}>{showSafety ? "Hide safety notes" : "Show safety notes"}</button>
        <button type="button" disabled={!input.trim()} onClick={onRecoveryDraft}>Create Recovery Draft</button>
      </div>
      {showSafety && (
        <MemorySummaryCard
          title="Safety notes"
          detail={(safetyNotes?.length ? safetyNotes : ["No hidden facts, NPC secrets, private persona, raw prompt, or API key in normal chat."]).join("; ")}
        />
      )}
      <div className="tavern-card-meta">
        {(memoryHints?.length ? memoryHints : ["No RP memory hints loaded."]).map((hint) => <span key={hint}>{safeExcerpt(hint, 80)}</span>)}
      </div>
      <div className="tavern-filter-row">
        <input value={messageSearch} onChange={(event) => setMessageSearch(event.target.value)} placeholder="Search safe message metadata" />
        <select value={messagePageSize} onChange={(event) => setMessagePageSize(Number(event.target.value))}>
          {[25, 50, 100].map((size) => <option key={size} value={size}>{size} rows</option>)}
        </select>
        <button type="button" onClick={jumpToLatestMessage} disabled={filteredMessages.length === 0}>Jump to latest</button>
        {messageSearch !== debouncedMessageSearch ? <span className="tavern-chip">filtering...</span> : null}
      </div>
      {messages.length ? (
        <>
          <p className="muted">Rendering {filteredMessages.length ? messageWindowStart + 1 : 0}-{messageWindowEnd} of {filteredMessages.length} safe message(s).</p>
          <div data-windowed-tavern-messages="true">
            {visibleMessages.length ? visibleMessages.map((message) => <RPMessageBubble key={message.message_id} message={message} />) : <p className="muted">No messages match this safe search.</p>}
          </div>
          {filteredMessages.length > messagePageSize ? (
            <div className="pagination-controls" aria-label="Tavern message pagination">
              <button type="button" onClick={() => setMessagePageIndex(0)} disabled={clampedMessagePageIndex === 0}>First</button>
              <button type="button" onClick={() => setMessagePageIndex(Math.max(clampedMessagePageIndex - 1, 0))} disabled={clampedMessagePageIndex === 0}>Previous</button>
              <span>Page {clampedMessagePageIndex + 1} / {messagePageCount}</span>
              <button type="button" onClick={() => setMessagePageIndex(Math.min(clampedMessagePageIndex + 1, messagePageCount - 1))} disabled={clampedMessagePageIndex >= messagePageCount - 1}>Next</button>
              <button type="button" onClick={() => setMessagePageIndex(messagePageCount - 1)} disabled={clampedMessagePageIndex >= messagePageCount - 1}>Last</button>
            </div>
          ) : null}
        </>
      ) : <p className="muted">No messages yet. Select a session and send a local RP line.</p>}
      <textarea value={input} onChange={(event) => onInputChange?.(event.target.value)} rows={3} placeholder="Write a local RP message..." />
      <button type="button" disabled={!session || !character || !input.trim()} onClick={onSend}>Send</button>
    </div>
  );
}

export function MultiNPCScenePro({ scenes, selectedSceneId, onSelect, onGenerateNext }: { scenes: MultiNPCSceneSummary[]; selectedSceneId?: string; onSelect?: (sceneId: string) => void; onGenerateNext?: () => void }) {
  const [sceneSearch, setSceneSearch] = useState("");
  const debouncedSceneSearch = useDebouncedValue(sceneSearch, 180);
  const [statusFilter, setStatusFilter] = useState("all");
  const [scenePageSize, setScenePageSize] = useState(12);
  const [scenePageIndex, setScenePageIndex] = useState(0);
  const [messagePageSize, setMessagePageSize] = useState(25);
  const [messagePageIndex, setMessagePageIndex] = useState(0);
  const selected = scenes.find((scene) => scene.scene_id === selectedSceneId) ?? scenes[0] ?? null;
  const statusOptions = useMemo(() => ["all", ...Array.from(new Set(scenes.map((scene) => scene.status || "draft"))).sort()], [scenes]);
  const sceneSearchIndexById = useMemo(
    () =>
      new Map(
        scenes.map((scene) => [
          scene.scene_id,
          buildSafeSearchIndex([
            scene.scene_id,
            scene.title,
            scene.status,
            scene.participant_ids.join(" "),
            scene.turn_order.join(" "),
            ...(scene.safety_notes ?? []).map((note) => safeExcerpt(note, 120))
          ])
        ])
      ),
    [scenes]
  );
  const filteredScenes = useMemo(
    () =>
      scenes.filter((scene) => {
        if (statusFilter !== "all" && (scene.status || "draft") !== statusFilter) return false;
        return !debouncedSceneSearch || safeSearchMatches(sceneSearchIndexById.get(scene.scene_id) ?? "", debouncedSceneSearch);
      }),
    [debouncedSceneSearch, sceneSearchIndexById, scenes, statusFilter]
  );
  const scenePageCount = Math.max(1, Math.ceil(filteredScenes.length / scenePageSize));
  const clampedScenePageIndex = Math.min(scenePageIndex, scenePageCount - 1);
  const sceneWindowStart = clampedScenePageIndex * scenePageSize;
  const sceneWindowEnd = Math.min(sceneWindowStart + scenePageSize, filteredScenes.length);
  const visibleScenes = filteredScenes.slice(sceneWindowStart, sceneWindowEnd);
  const selectedMessageIds = selected?.message_ids ?? [];
  const messagePageCount = Math.max(1, Math.ceil(selectedMessageIds.length / messagePageSize));
  const clampedMessagePageIndex = Math.min(messagePageIndex, messagePageCount - 1);
  const messageWindowStart = clampedMessagePageIndex * messagePageSize;
  const messageWindowEnd = Math.min(messageWindowStart + messagePageSize, selectedMessageIds.length);
  const visibleMessageIds = selectedMessageIds.slice(messageWindowStart, messageWindowEnd);

  useEffect(() => {
    setScenePageIndex(0);
  }, [debouncedSceneSearch, scenePageSize, scenes.length, statusFilter]);

  useEffect(() => {
    if (scenePageIndex > scenePageCount - 1) {
      setScenePageIndex(scenePageCount - 1);
    }
  }, [scenePageCount, scenePageIndex]);

  useEffect(() => {
    setMessagePageIndex(0);
  }, [messagePageSize, selected?.scene_id]);

  useEffect(() => {
    if (messagePageIndex > messagePageCount - 1) {
      setMessagePageIndex(messagePageCount - 1);
    }
  }, [messagePageCount, messagePageIndex]);

  return (
    <TavernSafeSummaryPanel title="Multi-NPC Scene Pro">
      {scenes.length === 0 ? <p className="muted">No multi-NPC scenes yet. Create at least two Tavern characters first.</p> : (
        <div className="multi-npc-scene-pro">
          <div className="tavern-filter-row">
            <input value={sceneSearch} onChange={(event) => setSceneSearch(event.target.value)} placeholder="Search scenes, participants, safe notes" />
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            <select value={scenePageSize} onChange={(event) => setScenePageSize(Number(event.target.value))}>
              {[6, 12, 24].map((size) => <option key={size} value={size}>{size} scenes</option>)}
            </select>
            {sceneSearch !== debouncedSceneSearch ? <span className="tavern-chip">filtering...</span> : null}
          </div>
          {filteredScenes.length === 0 ? <p className="muted">No multi-NPC scenes match this safe filter.</p> : (
          <>
          <p className="muted">Rendering {sceneWindowStart + 1}-{sceneWindowEnd} of {filteredScenes.length} scene(s).</p>
          <div className="tavern-card-grid" data-windowed-multi-npc-scenes="true">
            {visibleScenes.map((scene) => (
              <button key={scene.scene_id} type="button" className={`tavern-card ${scene.scene_id === selectedSceneId ? "selected-list-button" : ""}`} onClick={() => onSelect?.(scene.scene_id)}>
                <strong>{safeExcerpt(scene.title)}</strong>
                <span>{scene.status}</span>
                <span>participants {scene.participant_ids.length}</span>
                <span>turn {scene.current_turn_index + 1}</span>
              </button>
            ))}
          </div>
          {filteredScenes.length > scenePageSize ? (
            <div className="pagination-controls" aria-label="Multi-NPC scene pagination">
              <button type="button" onClick={() => setScenePageIndex(0)} disabled={clampedScenePageIndex === 0}>First</button>
              <button type="button" onClick={() => setScenePageIndex(Math.max(clampedScenePageIndex - 1, 0))} disabled={clampedScenePageIndex === 0}>Previous</button>
              <span>Page {clampedScenePageIndex + 1} / {scenePageCount}</span>
              <button type="button" onClick={() => setScenePageIndex(Math.min(clampedScenePageIndex + 1, scenePageCount - 1))} disabled={clampedScenePageIndex >= scenePageCount - 1}>Next</button>
              <button type="button" onClick={() => setScenePageIndex(scenePageCount - 1)} disabled={clampedScenePageIndex >= scenePageCount - 1}>Last</button>
            </div>
          ) : null}
          </>
          )}
          {selected && (
            <div className="tavern-scene-detail">
              <LinkedText title="Participants" values={selected.participant_ids} />
              <LinkedText title="Turn order" values={selected.turn_order} />
              <div className="tavern-filter-row">
                <span className="muted">Message refs {selectedMessageIds.length}</span>
                <select value={messagePageSize} onChange={(event) => setMessagePageSize(Number(event.target.value))}>
                  {[10, 25, 50].map((size) => <option key={size} value={size}>{size} refs</option>)}
                </select>
                <button type="button" onClick={() => setMessagePageIndex(Math.max(0, messagePageCount - 1))} disabled={selectedMessageIds.length === 0}>Jump to latest</button>
              </div>
              <LinkedText title={`Messages ${messageWindowStart + 1}-${messageWindowEnd}`} values={visibleMessageIds} />
              {selectedMessageIds.length > messagePageSize ? (
                <div className="pagination-controls" aria-label="Multi-NPC message ref pagination">
                  <button type="button" onClick={() => setMessagePageIndex(0)} disabled={clampedMessagePageIndex === 0}>First</button>
                  <button type="button" onClick={() => setMessagePageIndex(Math.max(clampedMessagePageIndex - 1, 0))} disabled={clampedMessagePageIndex === 0}>Previous</button>
                  <span>Page {clampedMessagePageIndex + 1} / {messagePageCount}</span>
                  <button type="button" onClick={() => setMessagePageIndex(Math.min(clampedMessagePageIndex + 1, messagePageCount - 1))} disabled={clampedMessagePageIndex >= messagePageCount - 1}>Next</button>
                  <button type="button" onClick={() => setMessagePageIndex(messagePageCount - 1)} disabled={clampedMessagePageIndex >= messagePageCount - 1}>Last</button>
                </div>
              ) : null}
              <p>Active speaker: {safeExcerpt(selected.turn_order[selected.current_turn_index] ?? "not set")}</p>
              <p>Knowledge-safe status: each NPC receives only character-safe and session-safe context; NPC unknown facts are excluded.</p>
              <button type="button" disabled={!selectedSceneId} onClick={onGenerateNext}>Generate Next Reply</button>
            </div>
          )}
        </div>
      )}
    </TavernSafeSummaryPanel>
  );
}

function LinkedText({ title, values }: { title: string; values?: string[] }) {
  return <p><strong>{title}:</strong> {(values ?? []).map((value) => safeExcerpt(value, 60)).join(", ") || "none"}</p>;
}

export function RPMemoryPanel({ sessions = [], recoveryRecords = [], matureVisible = false }: { sessions?: TavernSession[]; recoveryRecords?: TavernSessionRecoveryRecord[]; matureVisible?: boolean }) {
  const [memorySearch, setMemorySearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const debouncedMemorySearch = useDebouncedValue(memorySearch, 180);
  const [pageSize, setPageSize] = useState(8);
  const [pageIndex, setPageIndex] = useState(0);
  const rows = useMemo(
    () => [
      ...sessions.map((session) => ({ type: "relationship", title: session.title, detail: `${session.character_ids.length} character(s), ${session.message_count ?? 0} message(s), visibility tavern_safe` })),
      ...recoveryRecords.map((record) => ({ type: record.target_type, title: record.target_id, detail: safeExcerpt(record.safe_draft_text) }))
    ],
    [recoveryRecords, sessions]
  );
  const typeOptions = useMemo(() => ["all", ...Array.from(new Set(rows.map((row) => row.type))).sort()], [rows]);
  const memorySearchIndexByKey = useMemo(
    () =>
      new Map(
        rows.map((row) => [
          `${row.type}:${row.title}`,
          buildSafeSearchIndex([row.type, row.title, row.detail])
        ])
      ),
    [rows]
  );
  const filteredRows = useMemo(
    () =>
      rows.filter((row) => {
        if (typeFilter !== "all" && row.type !== typeFilter) return false;
        return !debouncedMemorySearch || safeSearchMatches(memorySearchIndexByKey.get(`${row.type}:${row.title}`) ?? "", debouncedMemorySearch);
      }),
    [debouncedMemorySearch, memorySearchIndexByKey, rows, typeFilter]
  );
  const pageCount = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, filteredRows.length);
  const visibleRows = filteredRows.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [debouncedMemorySearch, pageSize, rows.length, typeFilter]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  return (
    <TavernSafeSummaryPanel title="RP Memory Panel">
      <div className="tavern-card-meta">
        {["relationship", "promise", "preference", "mood", "boundary", matureVisible ? "mature_only opt-in" : "mature_only hidden"].map((item) => <span key={item}>{item}</span>)}
      </div>
      <div className="tavern-filter-row">
        <input value={memorySearch} onChange={(event) => setMemorySearch(event.target.value)} placeholder="Search safe memory metadata" />
        <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
          {typeOptions.map((type) => <option key={type} value={type}>{type}</option>)}
        </select>
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[8, 16, 32].map((size) => <option key={size} value={size}>{size} rows</option>)}
        </select>
        {memorySearch !== debouncedMemorySearch ? <span className="tavern-chip">filtering...</span> : null}
      </div>
      {rows.length === 0 ? <p className="muted">No safe RP memory rows yet.</p> : filteredRows.length === 0 ? <p className="muted">No safe RP memory rows match this filter.</p> : (
        <div data-windowed-rp-memory="true">
          <p className="muted">Rendering {windowStart + 1}-{windowEnd} of {filteredRows.length} safe RP memory row(s).</p>
          {visibleRows.map((row) => <MemorySummaryCard key={`${row.type}-${row.title}`} title={`${row.type}: ${row.title}`} detail={row.detail} />)}
          {filteredRows.length > pageSize ? (
            <div className="pagination-controls" aria-label="RP memory pagination">
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>First</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>Previous</button>
              <span>Page {clampedPageIndex + 1} / {pageCount}</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>Next</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>Last</button>
            </div>
          ) : null}
        </div>
      )}
      <p className="muted">Archive/delete actions require confirmation; hidden/debug/mature-only memory is not shown in normal view.</p>
    </TavernSafeSummaryPanel>
  );
}

export function EmotionArcPanel({ messages = [] }: { messages?: TavernMessage[] }) {
  const recent = messages.slice(-4);
  return (
    <TavernSafeSummaryPanel title="Emotion Arc Panel">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="Current EmotionState" detail="primary emotion: calm / secondary: attentive / intensity: low / valence: neutral / arousal: low" />
        <MemorySummaryCard title="Triggers safe summary" detail={recent.length ? recent.map((message) => `${message.speaker_type}:${message.message_id}`).join(", ") : "No recent safe trigger refs."} />
      </div>
      <details>
        <summary>Authoring note (authoring-only)</summary>
        <p className="muted">Authoring notes are not sent to normal Tavern prompt context unless explicitly allowed by safe policy.</p>
      </details>
    </TavernSafeSummaryPanel>
  );
}

export function RelationshipTonePanel({ characters = [], sessions = [], onPropose }: { characters?: TavernCharacter[]; sessions?: TavernSession[]; onPropose?: () => void }) {
  const pairs = sessions.flatMap((session) => session.character_ids.slice(0, 2).length >= 2 ? [{ a: session.character_ids[0], b: session.character_ids[1], source: "tavern memory" }] : []);
  return (
    <TavernSafeSummaryPanel title="Relationship Tone Panel">
      {pairs.length === 0 ? <p className="muted">No relationship pairs yet. Add multiple characters to a session or scene.</p> : pairs.map((pair) => (
        <div key={`${pair.a}-${pair.b}`} className="memory-summary-card">
          <strong>{safeExcerpt(pair.a)} ↔ {safeExcerpt(pair.b)}</strong>
          <p>trust medium · affinity neutral · fear low · respect medium · tension low · resentment hidden by default · protectiveness unknown</p>
          <p className="muted">Source: {pair.source}. Hidden world relationships and mature/intimacy fields are not shown.</p>
        </div>
      ))}
      <p className="muted">Loaded characters: {characters.length}. Propose change creates {"Tavern -> World"} proposal only.</p>
      <button type="button" onClick={onPropose}>Propose relationship change</button>
    </TavernSafeSummaryPanel>
  );
}

export function SceneMoodPresetPanel({ presets, selectedPresetId, onSelect, onCreate }: { presets: TavernScenePreset[]; selectedPresetId?: string; onSelect?: (presetId: string) => void; onCreate?: () => void }) {
  return (
    <TavernSafeSummaryPanel title="Scene Mood UI / Scene Mood Preset UI">
      <p>Scene mood only affects expression and does not change world facts. Fade-to-black policy remains safe by default.</p>
      <button type="button" onClick={onCreate}>Create local preset</button>
      {presets.length === 0 ? <p className="muted">No scene mood presets yet.</p> : presets.map((preset) => (
        <button key={preset.preset_id} type="button" className={`tavern-card ${preset.preset_id === selectedPresetId ? "selected-list-button" : ""}`} onClick={() => onSelect?.(preset.preset_id)}>
          <SceneMoodBadge preset={preset} />
          <span>pacing {preset.pacing || "default"} · sensory {(preset.sensory_focus ?? []).join(", ") || "none"} · emotional {preset.emotional_tone || "neutral"}</span>
        </button>
      ))}
    </TavernSafeSummaryPanel>
  );
}

export function CharacterVoiceLabPanel({ character }: { character?: TavernCharacter | null }) {
  return (
    <TavernSafeSummaryPanel title="Character Voice Lab UI">
      <div className="tavern-editor-grid">
        <label>Tone<input readOnly value={character?.voice_profile_id ? "profile-linked text voice" : "draft tone"} /></label>
        <label>Diction<input readOnly value="safe vocabulary and sentence rhythm only" /></label>
        <label>Catchphrases<input readOnly value="add local safe samples in VoiceProfile editor" /></label>
        <label>Taboo phrases<input readOnly value="private notes excluded from normal preview" /></label>
      </div>
      <p>Text voice only. No TTS, no real provider call, and private notes are not shown in normal preview.</p>
    </TavernSafeSummaryPanel>
  );
}

export function BoundaryMatureSettingsPanel({ preferences }: { preferences?: TavernPreferences | null }) {
  return (
    <TavernSafeSummaryPanel title="Boundary / Mature Settings UI">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="Mature enabled" detail="enabled=false by default; visible setting remains off unless explicitly changed." />
        <MemorySummaryCard title="Export mature content" detail="false by default; mature/private content is excluded from normal export." />
        <MemorySummaryCard title="No minors / unknown age" detail="Unknown age or minor characters are blocked from mature scenes." />
        <MemorySummaryCard title="Consent required" detail="Consent and provider policy requirements must pass before selected rating." />
      </div>
      <p className="muted">Current mature panel visible: {preferences?.mature_module_visible ? "opt-in visible" : "off / hidden"}.</p>
    </TavernSafeSummaryPanel>
  );
}

export function TavernPromptProviderPanel({ promptProfileId, providerProfileId, modelId, useCase = "tavern_reply" }: { promptProfileId?: string | null; providerProfileId?: string | null; modelId?: string | null; useCase?: string }) {
  return (
    <TavernSafeSummaryPanel title="Tavern Prompt / Provider">
      <p>Prompt profile: {promptProfileId || "tavern default"}</p>
      <p>Provider profile: {providerProfileId || "Provider Gateway safe route"}</p>
      <p>Model id: {modelId || "safe default / mock for tests"}</p>
      <p>Use case: {useCase}. Provider safety policy and mature routing status are safe summaries only.</p>
      <p>API key not shown, raw prompt hidden, hidden facts and NPC secrets excluded.</p>
    </TavernSafeSummaryPanel>
  );
}

export function RPSafetyDashboardPanel({ report, onRun }: { report?: RPSafetyDashboardReport | null; onRun?: () => void }) {
  const categories = ["hidden facts", "NPC secrets / knowledge", "private persona", "mature memory", "provider safety routing", "world consistency", "proposal validation", "export safety"];
  return (
    <TavernSafeSummaryPanel title="RP Safety Dashboard">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="Overall status" detail={report ? `${report.overall_status}; blockers ${report.blocker_count}; warnings ${report.warning_count}` : "not_run"} />
        <MemorySummaryCard title="Safety categories" detail={categories.join("; ")} />
      </div>
      <button type="button" onClick={onRun}>Run RP Safety Eval</button>
      {report?.issues.length ? report.issues.map((issue) => (
        <div key={`${issue.category}-${issue.safe_summary}`} className="memory-summary-card">
          <strong>{issue.severity} · {issue.category}</strong>
          <p>{safeExcerpt(issue.safe_summary)}</p>
          <p className="muted">Affected: {issue.affected_session_id || issue.affected_character_id || "project"} · Suggested action: {safeExcerpt(issue.suggested_action)}</p>
        </div>
      )) : <p className="muted">No RP safety report yet. Run the local eval to inspect hidden leaks, NPC knowledge, mature boundary, and provider routing.</p>}
    </TavernSafeSummaryPanel>
  );
}

export function TavernCrossModeSafetyPanel({ worldNpcs, exportPreview }: { worldNpcs?: WorldNpcSafeSummary[]; exportPreview?: TavernSessionExportPreview | null }) {
  return (
    <TavernSafeSummaryPanel title="Cross-Mode / Export Safety">
      <p>{"Tavern -> World"} remains proposal / validation / dry-run / explicit confirm. {"Tavern -> Novel"} creates filtered scene drafts only.</p>
      <p>{"World NPC -> Tavern"} player_safe excludes NPC secrets and unknown facts.</p>
      <LinkedText title="safe World NPC refs" values={(worldNpcs ?? []).map((npc) => `${npc.display_name}:${npc.npc_id}`)} />
      <p>Export preview: {exportPreview ? `${exportPreview.session_count} session(s), ${exportPreview.message_count} safe message(s), ${exportPreview.excluded_items.length} excluded item(s)` : "not run"}</p>
      <p>Filtering policy: {(exportPreview?.filtering_policy ?? ["API key excluded", "hidden facts excluded", "NPC secrets excluded", "mature/private excluded by default", "debug data excluded"]).join("; ")}</p>
    </TavernSafeSummaryPanel>
  );
}
