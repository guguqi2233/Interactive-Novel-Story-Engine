import { ReactNode } from "react";
import { MultiNPCSceneSummary, TavernCharacter, TavernMessage, TavernScenePreset, TavernSession } from "./api";

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
  return (
    <button type="button" className={`tavern-card tavern-character-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <strong>{safeExcerpt(character.display_name, 80)}</strong>
      <p className="muted">{safeExcerpt(character.description) || "Project-local Tavern character draft."}</p>
      <div className="tavern-card-meta">
        <span>{character.linked_world_npc_id ? `world ref ${character.linked_world_npc_id}` : "no world ref"}</span>
        <RPSafetyBadge status={(character.safety_flags ?? []).length ? "review" : "safe"} />
      </div>
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

export function CharacterCardLibrary({ characters, onSelect }: { characters: TavernCharacter[]; onSelect?: (id: string) => void }) {
  return <div className="tavern-card-grid">{characters.map((character) => <TavernCharacterCard key={character.tavern_character_id} character={character} onSelect={() => onSelect?.(character.tavern_character_id)} />)}</div>;
}

export function TavernCharacterEditor() {
  return <TavernSafeSummaryPanel title="Tavern Character Editor"><p>Public character, RP, voice, example dialogue, and boundary refs can be edited locally. Private persona is authoring-only.</p></TavernSafeSummaryPanel>;
}

export function SingleCharacterChatPro({ messages }: { messages: TavernMessage[] }) {
  return <div className="single-character-chat-pro">{messages.length ? messages.map((message) => <RPMessageBubble key={message.message_id} message={message} />) : <p className="muted">No messages yet.</p>}</div>;
}

export function MultiNPCScenePro({ scenes }: { scenes: MultiNPCSceneSummary[] }) {
  return <div className="multi-npc-scene-pro">{scenes.map((scene) => <MemorySummaryCard key={scene.scene_id} title={scene.title} detail={`participants ${scene.participant_ids.length}; turn ${scene.current_turn_index + 1}`} />)}</div>;
}

export function RPMemoryPanel() {
  return <TavernSafeSummaryPanel title="RP Memory Panel"><p>Relationship, promise, preference, mood, and boundary memory are shown as safe summaries. Mature-only memory is hidden by default.</p></TavernSafeSummaryPanel>;
}

export function EmotionArcPanel() {
  return <TavernSafeSummaryPanel title="Emotion Arc Panel"><p>Emotion arcs affect Tavern prompt context only and do not modify World NPCs.</p></TavernSafeSummaryPanel>;
}

export function RelationshipTonePanel() {
  return <TavernSafeSummaryPanel title="Relationship Tone Panel"><p>Relationship tone is proposal-only for World changes and shows safe summaries.</p></TavernSafeSummaryPanel>;
}

export function SceneMoodPresetPanel({ presets }: { presets: TavernScenePreset[] }) {
  return <TavernSafeSummaryPanel title="Scene Mood UI">{presets.map((preset) => <p key={preset.preset_id}><SceneMoodBadge preset={preset} /></p>)}</TavernSafeSummaryPanel>;
}

export function CharacterVoiceLabPanel() {
  return <TavernSafeSummaryPanel title="Character Voice Lab UI"><p>Text voice only: tone, diction, catchphrases, taboo phrases, and safe samples. No TTS and no real provider call by default.</p></TavernSafeSummaryPanel>;
}

export function BoundaryMatureSettingsPanel() {
  return <TavernSafeSummaryPanel title="Boundary / Mature Settings UI"><p>Mature Module is disabled by default. Consent is required, unknown/minor scenes are blocked, and mature export is default off.</p></TavernSafeSummaryPanel>;
}

export function TavernPromptProviderPanel() {
  return <TavernSafeSummaryPanel title="Tavern Prompt / Provider"><p>Provider Gateway safe summary only. API key not shown, raw prompt hidden, and NPC secrets excluded.</p></TavernSafeSummaryPanel>;
}

export function RPSafetyDashboardPanel() {
  return <TavernSafeSummaryPanel title="RP Safety Dashboard"><p>Hidden leaks, NPC knowledge, private persona, mature memory, provider routing, world consistency, proposal validation, and export safety use safe issue rows.</p></TavernSafeSummaryPanel>;
}
