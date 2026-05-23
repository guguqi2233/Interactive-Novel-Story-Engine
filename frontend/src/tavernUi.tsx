import { ReactNode, useMemo, useState } from "react";
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
  const [filter, setFilter] = useState("all");
  const filtered = characters.filter((character) => {
    const haystack = [
      character.display_name,
      character.description,
      character.linked_character_profile_id,
      character.linked_world_npc_id,
      character.rp_profile_id,
      character.voice_profile_id,
      ...(character.safety_flags ?? [])
    ].join(" ").toLowerCase();
    const matchesQuery = !query || haystack.includes(query.toLowerCase());
    const matchesFilter =
      filter === "all" ||
      (filter === "linked_world" && Boolean(character.linked_world_npc_id)) ||
      (filter === "needs_profile" && (!character.rp_profile_id || !character.voice_profile_id)) ||
      (filter === "safety_review" && Boolean(character.safety_flags?.length));
    return matchesQuery && matchesFilter;
  });
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
      {messages.length ? messages.map((message) => <RPMessageBubble key={message.message_id} message={message} />) : <p className="muted">No messages yet. Select a session and send a local RP line.</p>}
      <textarea value={input} onChange={(event) => onInputChange?.(event.target.value)} rows={3} placeholder="Write a local RP message..." />
      <button type="button" disabled={!session || !character || !input.trim()} onClick={onSend}>Send</button>
    </div>
  );
}

export function MultiNPCScenePro({ scenes, selectedSceneId, onSelect, onGenerateNext }: { scenes: MultiNPCSceneSummary[]; selectedSceneId?: string; onSelect?: (sceneId: string) => void; onGenerateNext?: () => void }) {
  const selected = scenes.find((scene) => scene.scene_id === selectedSceneId) ?? scenes[0] ?? null;
  return (
    <TavernSafeSummaryPanel title="Multi-NPC Scene Pro">
      {scenes.length === 0 ? <p className="muted">No multi-NPC scenes yet. Create at least two Tavern characters first.</p> : (
        <div className="multi-npc-scene-pro">
          <div className="tavern-card-grid">
            {scenes.map((scene) => (
              <button key={scene.scene_id} type="button" className={`tavern-card ${scene.scene_id === selectedSceneId ? "selected-list-button" : ""}`} onClick={() => onSelect?.(scene.scene_id)}>
                <strong>{safeExcerpt(scene.title)}</strong>
                <span>{scene.status}</span>
                <span>participants {scene.participant_ids.length}</span>
                <span>turn {scene.current_turn_index + 1}</span>
              </button>
            ))}
          </div>
          {selected && (
            <div className="tavern-scene-detail">
              <LinkedText title="Participants" values={selected.participant_ids} />
              <LinkedText title="Turn order" values={selected.turn_order} />
              <LinkedText title="Messages" values={selected.message_ids} />
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
  const rows = [
    ...sessions.map((session) => ({ type: "relationship", title: session.title, detail: `${session.character_ids.length} character(s), ${session.message_count ?? 0} message(s), visibility tavern_safe` })),
    ...recoveryRecords.map((record) => ({ type: record.target_type, title: record.target_id, detail: safeExcerpt(record.safe_draft_text) }))
  ];
  return (
    <TavernSafeSummaryPanel title="RP Memory Panel">
      <div className="tavern-card-meta">
        {["relationship", "promise", "preference", "mood", "boundary", matureVisible ? "mature_only opt-in" : "mature_only hidden"].map((item) => <span key={item}>{item}</span>)}
      </div>
      {rows.length === 0 ? <p className="muted">No safe RP memory rows yet.</p> : rows.slice(0, 8).map((row) => <MemorySummaryCard key={`${row.type}-${row.title}`} title={`${row.type}: ${row.title}`} detail={row.detail} />)}
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
