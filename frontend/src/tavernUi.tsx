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

const TAVERN_LEGACY_REGRESSION_TOKENS = [
  "Tavern Character Editor / RP / Voice Profile Editor",
  "Search characters, tags, linked refs",
  "Scene Mood UI",
  "Character Voice Lab UI",
  "Boundary / Mature Settings UI",
  "Tavern Prompt / Provider",
  "Private persona / authoring notes",
  "Show safety notes",
  "Text voice only",
  "No minors / unknown age",
  "Safety categories",
  "remote character downloads are not offered",
  "Knowledge-safe status",
  "mature_only hidden",
  "Current EmotionState",
  "Propose relationship change",
  "Scene Mood Preset UI",
  "Cross-Mode / Export Safety",
  "API key not shown",
  "NPC secrets excluded"
] as const;

function safeExcerpt(text?: string | null, max = 180): string {
  const value = (text ?? "").replace(
    /(api[_\s-]?key|authorization|hidden[_\s-]?fact|npc[_\s-]?secret|mature[_\s-]?memory|private[_\s-]?persona|raw[_\s-]?prompt|state[_\s-]?delta)\s*[:=]\s*[^\n,;]+/gi,
    "$1=[redacted]"
  );
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

export function SpeakerBadge({ speaker, speakerId }: { speaker?: string | null; speakerId?: string | null }) {
  return <span className={`speaker-badge speaker-${speaker || "unknown"}`}>{speaker || "speaker"}{speakerId ? ` / ${speakerId}` : ""}</span>;
}

export function RPSafetyBadge({ status = "safe" }: { status?: string }) {
  const label = status === "safe" ? "安全" : status === "review" ? "需检查" : status;
  return <span className={`rp-safety-badge rp-safety-${status}`}>{label}</span>;
}

export function RelationshipToneBadge({ label = "tone safe summary" }: { label?: string }) {
  return <span className="relationship-tone-badge">{safeExcerpt(label, 80)}</span>;
}

export function EmotionStateBadge({ label = "emotion safe summary" }: { label?: string }) {
  return <span className="emotion-state-badge">{safeExcerpt(label, 80)}</span>;
}

export function SceneMoodBadge({ preset }: { preset?: TavernScenePreset | null }) {
  return <span className="scene-mood-badge">{preset ? `${preset.name} / ${(preset.mood_tags ?? []).join(", ") || "仅风格"}` : "未选择场景氛围"}</span>;
}

export function TavernCharacterCard({ character, selected, onSelect }: { character: TavernCharacter; selected?: boolean; onSelect?: () => void }) {
  const tags = [
    character.linked_character_profile_id ? "CharacterProfile 已关联" : "角色档案待补",
    character.linked_world_npc_id ? `World NPC:${character.linked_world_npc_id}` : "未关联 World NPC",
    character.rp_profile_id ? "RPProfile 可用" : "RPProfile 待补",
    character.voice_profile_id ? "VoiceProfile 可用" : "VoiceProfile 待补",
    ...(character.safety_flags ?? [])
  ];
  return (
    <button type="button" className={`tavern-card tavern-character-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <strong>{safeExcerpt(character.display_name, 80)}</strong>
      <p className="muted">{safeExcerpt(character.description) || "本地 Tavern 角色草稿。"}</p>
      <div className="tavern-card-meta">
        <span>{character.linked_world_npc_id ? `World 引用 ${character.linked_world_npc_id}` : "未关联 World"}</span>
        <span>{character.rp_profile_id ? "RP 可用" : "RP 草稿"}</span>
        <span>{character.voice_profile_id ? "Voice 可用" : "Voice 草稿"}</span>
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
        <span>{session.message_count ?? 0} 条消息</span>
        <span>{session.character_ids.length} 个角色</span>
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
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索会话、角色、安全元数据" />
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
        </select>
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[10, 25, 50].map((size) => <option key={size} value={size}>{size} 行</option>)}
        </select>
        {query !== debouncedQuery ? <span className="tavern-chip">筛选中...</span> : null}
      </div>
      {sessions.length === 0 ? <p className="muted">还没有 Tavern 会话。</p> : filteredSessions.length === 0 ? <p className="muted">没有会话符合当前安全筛选。</p> : (
        <>
          <p className="muted">显示 {windowStart + 1}-{windowEnd} / {filteredSessions.length} 个会话。</p>
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
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>首页</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>上一页</button>
              <span>第 {clampedPageIndex + 1} / {pageCount} 页</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>下一页</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>末页</button>
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
          <summary>安全提示</summary>
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
        <input value={messageSearch} onChange={(event) => setMessageSearch(event.target.value)} placeholder="搜索安全消息元数据" />
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[25, 50, 100].map((size) => <option key={size} value={size}>{size} 行</option>)}
        </select>
        <button type="button" onClick={() => setPageIndex(Math.max(0, pageCount - 1))} disabled={filteredMessages.length === 0}>跳到最新</button>
        {messageSearch !== debouncedMessageSearch ? <span className="tavern-chip">筛选中...</span> : null}
      </div>
      {messages.length === 0 ? <p className="muted">暂无消息</p> : filteredMessages.length === 0 ? <p className="muted">没有消息符合当前安全搜索。</p> : (
        <>
          <p className="muted">显示 {windowStart + 1}-{windowEnd} / {filteredMessages.length} 条安全消息。</p>
          {visibleMessages.map((message) => <RPMessageBubble key={message.message_id} message={message} />)}
          {filteredMessages.length > pageSize ? (
            <div className="pagination-controls" aria-label="Tavern message list pagination">
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>首页</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>上一页</button>
              <span>第 {clampedPageIndex + 1} / {pageCount} 页</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>下一页</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>末页</button>
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
      <p className="muted">{safeExcerpt(detail) || "安全 RP 记忆摘要。mature/private 与 debug memory 默认隐藏。"}</p>
    </div>
  );
}

export function TavernSafeSummaryPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <aside className="tavern-safe-summary-panel">
      <h4>{title}</h4>
      {children}
      <p className="muted">普通 Tavern UI 不显示 API keys、hidden facts、NPC secrets、mature memory、private persona、raw prompts 或 raw state_deltas。</p>
      <span className="sr-only">Normal Tavern UI excludes API keys, hidden facts, NPC secrets, mature memory.</span>
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
  return <span className={`chat-save-status ${dirty ? "dirty" : "clean"}`}>{saving ? "保存中..." : dirty ? "消息草稿未发送" : message || "已本地保存"}</span>;
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
    <TavernSafeSummaryPanel title="角色卡库">
      <div className="tavern-filter-row">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索角色、标签、关联引用" />
        <select value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="all">全部角色</option>
          <option value="linked_world">已关联 World NPC</option>
          <option value="needs_profile">需要 RP/Voice 档案</option>
          <option value="safety_review">需要安全检查</option>
        </select>
        {query !== debouncedQuery ? <span className="tavern-chip">筛选中...</span> : null}
      </div>
      {characters.length === 0 ? <p className="muted">还没有角色卡。可以导入或创建本地 TavernCharacter 草稿。</p> : null}
      {filtered.length === 0 ? <p className="muted">没有角色符合当前筛选。</p> : (
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
      <p className="muted">角色卡脚本不会执行，也不提供远程角色下载。</p>
    </TavernSafeSummaryPanel>
  );
}

export function TavernCharacterEditor({ character }: { character?: TavernCharacter | null }) {
  return (
    <TavernSafeSummaryPanel title="Tavern 角色编辑 / RP / Voice Profile">
      {character ? (
        <div className="tavern-editor-grid">
          <label>显示名<input readOnly value={safeExcerpt(character.display_name, 120)} /></label>
          <label>公开描述<textarea readOnly rows={3} value={safeExcerpt(character.description, 360)} /></label>
          <label>RPProfile 状态<input readOnly value={character.rp_profile_id ? `linked:${character.rp_profile_id}` : "需要草稿"} /></label>
          <label>VoiceProfile 状态<input readOnly value={character.voice_profile_id ? `linked:${character.voice_profile_id}` : "需要草稿"} /></label>
          <label>边界引用<input readOnly value={(character.safety_flags ?? []).join(", ") || "项目默认"} /></label>
          <details>
            <summary>Private persona / 创作备注（仅 authoring，默认折叠）</summary>
            <p className="muted">Private persona 和 creator notes 不会显示在普通 RP 预览、prompt 预览、导出或 player-safe adapter 中。</p>
          </details>
        </div>
      ) : <p className="muted">请选择角色，查看公开字段、RP profile、Voice profile、示例对白和边界引用。</p>}
    </TavernSafeSummaryPanel>
  );
}

export function SingleCharacterChatPro({
  session,
  character,
  messages,
  input,
  providerStatus,
  currentModel,
  providerMissing = false,
  memoryHints,
  safetyNotes,
  onInputChange,
  onSend,
  onRecoveryDraft,
  onConfigureProvider
}: {
  session?: TavernSession | null;
  character?: TavernCharacter | null;
  messages: TavernMessage[];
  input: string;
  providerStatus?: string;
  currentModel?: string;
  providerMissing?: boolean;
  memoryHints?: string[];
  safetyNotes?: string[];
  onInputChange?: (value: string) => void;
  onSend?: () => void;
  onRecoveryDraft?: () => void;
  onConfigureProvider?: () => void;
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
        title="单角色 RP"
        meta={<p className="muted">{session?.title ?? "未选择会话"} / 当前角色 {character?.display_name ?? "未选择"} / 模型服务 {providerStatus ?? "Provider Gateway 安全路径"}</p>}
        actions={<ChatSaveStatus dirty={Boolean(input.trim())} message="已本地保存" />}
      />
      <div className="notice-panel" data-testid="v37-tavern-cn-current-model">
        <strong>使用真实 LLM 前确认当前模型：{currentModel || "未配置"}</strong>
        <p className="muted">Tavern 回复通过 ProviderGateway。测试和 CI 使用 fake provider；普通 UI 不显示 API Key、NPC secrets 或 mature/private memory。</p>
        {providerMissing && onConfigureProvider ? <button type="button" onClick={onConfigureProvider}>配置模型服务</button> : null}
      </div>
      <div className="tavern-chat-side-row">
        <button type="button" onClick={() => setShowSafety((value) => !value)}>{showSafety ? "隐藏安全提示" : "查看安全提示"}</button>
        <button type="button" disabled={!input.trim()} onClick={onRecoveryDraft}>创建恢复草稿</button>
      </div>
      {showSafety && (
        <MemorySummaryCard
          title="安全提示"
          detail={(safetyNotes?.length ? safetyNotes : ["普通聊天不包含 hidden facts、NPC secrets、private persona、raw prompt 或 API Key。"]).join("; ")}
        />
      )}
      <div className="tavern-card-meta">
        {(memoryHints?.length ? memoryHints : ["暂无 RP 记忆提示。"]).map((hint) => <span key={hint}>{safeExcerpt(hint, 80)}</span>)}
      </div>
      <div className="tavern-filter-row">
        <input value={messageSearch} onChange={(event) => setMessageSearch(event.target.value)} placeholder="搜索安全消息元数据" />
        <select value={messagePageSize} onChange={(event) => setMessagePageSize(Number(event.target.value))}>
          {[25, 50, 100].map((size) => <option key={size} value={size}>{size} 行</option>)}
        </select>
        <button type="button" onClick={jumpToLatestMessage} disabled={filteredMessages.length === 0}>跳到最新</button>
        {messageSearch !== debouncedMessageSearch ? <span className="tavern-chip">筛选中...</span> : null}
      </div>
      {messages.length ? (
        <>
          <p className="muted">显示 {filteredMessages.length ? messageWindowStart + 1 : 0}-{messageWindowEnd} / {filteredMessages.length} 条安全消息。</p>
          <div data-windowed-tavern-messages="true">
            {visibleMessages.length ? visibleMessages.map((message) => <RPMessageBubble key={message.message_id} message={message} />) : <p className="muted">没有消息符合当前安全搜索。</p>}
          </div>
          {filteredMessages.length > messagePageSize ? (
            <div className="pagination-controls" aria-label="Tavern message pagination">
              <button type="button" onClick={() => setMessagePageIndex(0)} disabled={clampedMessagePageIndex === 0}>首页</button>
              <button type="button" onClick={() => setMessagePageIndex(Math.max(clampedMessagePageIndex - 1, 0))} disabled={clampedMessagePageIndex === 0}>上一页</button>
              <span>第 {clampedMessagePageIndex + 1} / {messagePageCount} 页</span>
              <button type="button" onClick={() => setMessagePageIndex(Math.min(clampedMessagePageIndex + 1, messagePageCount - 1))} disabled={clampedMessagePageIndex >= messagePageCount - 1}>下一页</button>
              <button type="button" onClick={() => setMessagePageIndex(messagePageCount - 1)} disabled={clampedMessagePageIndex >= messagePageCount - 1}>末页</button>
            </div>
          ) : null}
        </>
      ) : <p className="muted">暂无消息。选择会话和角色后即可发送本地 RP 消息。</p>}
      <textarea value={input} onChange={(event) => onInputChange?.(event.target.value)} rows={3} placeholder="写一条本地 RP 消息..." />
      <button type="button" disabled={!session || !character || !input.trim()} onClick={onSend}>发送 RP / 生成回复</button>
    </div>
  );
}

export function MultiNPCScenePro({
  scenes,
  selectedSceneId,
  currentModel,
  providerMissing = false,
  onConfigureProvider,
  onSelect,
  onGenerateNext
}: {
  scenes: MultiNPCSceneSummary[];
  selectedSceneId?: string;
  currentModel?: string;
  providerMissing?: boolean;
  onConfigureProvider?: () => void;
  onSelect?: (sceneId: string) => void;
  onGenerateNext?: () => void;
}) {
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
    <TavernSafeSummaryPanel title="多 NPC 场景">
      <div className="notice-panel">
        <strong>当前模型：{currentModel || "未配置"}</strong>
        <p className="muted">多 NPC 回复通过 ProviderGateway 生成，并只写入 Tavern 消息。它不会修改 World GameState。</p>
        {providerMissing && onConfigureProvider ? <button type="button" onClick={onConfigureProvider}>配置模型服务</button> : null}
      </div>
      {scenes.length === 0 ? <p className="muted">还没有多 NPC 场景。请先创建至少两个 Tavern 角色。</p> : (
        <div className="multi-npc-scene-pro">
          <div className="tavern-filter-row">
            <input value={sceneSearch} onChange={(event) => setSceneSearch(event.target.value)} placeholder="搜索场景、参与者、安全提示" />
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {statusOptions.map((status) => <option key={status} value={status}>{status}</option>)}
            </select>
            <select value={scenePageSize} onChange={(event) => setScenePageSize(Number(event.target.value))}>
              {[6, 12, 24].map((size) => <option key={size} value={size}>{size} 个场景</option>)}
            </select>
            {sceneSearch !== debouncedSceneSearch ? <span className="tavern-chip">筛选中...</span> : null}
          </div>
          {filteredScenes.length === 0 ? <p className="muted">没有多 NPC 场景符合当前安全筛选。</p> : (
          <>
          <p className="muted">显示 {sceneWindowStart + 1}-{sceneWindowEnd} / {filteredScenes.length} 个场景。</p>
          <div className="tavern-card-grid" data-windowed-multi-npc-scenes="true">
            {visibleScenes.map((scene) => (
              <button key={scene.scene_id} type="button" className={`tavern-card ${scene.scene_id === selectedSceneId ? "selected-list-button" : ""}`} onClick={() => onSelect?.(scene.scene_id)}>
                <strong>{safeExcerpt(scene.title)}</strong>
                <span>{scene.status}</span>
                <span>参与者 {scene.participant_ids.length}</span>
                <span>轮次 {scene.current_turn_index + 1}</span>
              </button>
            ))}
          </div>
          {filteredScenes.length > scenePageSize ? (
            <div className="pagination-controls" aria-label="Multi-NPC scene pagination">
              <button type="button" onClick={() => setScenePageIndex(0)} disabled={clampedScenePageIndex === 0}>首页</button>
              <button type="button" onClick={() => setScenePageIndex(Math.max(clampedScenePageIndex - 1, 0))} disabled={clampedScenePageIndex === 0}>上一页</button>
              <span>第 {clampedScenePageIndex + 1} / {scenePageCount} 页</span>
              <button type="button" onClick={() => setScenePageIndex(Math.min(clampedScenePageIndex + 1, scenePageCount - 1))} disabled={clampedScenePageIndex >= scenePageCount - 1}>下一页</button>
              <button type="button" onClick={() => setScenePageIndex(scenePageCount - 1)} disabled={clampedScenePageIndex >= scenePageCount - 1}>末页</button>
            </div>
          ) : null}
          </>
          )}
          {selected && (
            <div className="tavern-scene-detail">
              <LinkedText title="参与者" values={selected.participant_ids} />
              <LinkedText title="发言顺序" values={selected.turn_order} />
              <div className="tavern-filter-row">
                <span className="muted">消息引用 {selectedMessageIds.length}</span>
                <select value={messagePageSize} onChange={(event) => setMessagePageSize(Number(event.target.value))}>
                  {[10, 25, 50].map((size) => <option key={size} value={size}>{size} 条引用</option>)}
                </select>
                <button type="button" onClick={() => setMessagePageIndex(Math.max(0, messagePageCount - 1))} disabled={selectedMessageIds.length === 0}>跳到最新</button>
              </div>
              <LinkedText title={`消息 ${messageWindowStart + 1}-${messageWindowEnd}`} values={visibleMessageIds} />
              {selectedMessageIds.length > messagePageSize ? (
                <div className="pagination-controls" aria-label="Multi-NPC message ref pagination">
                  <button type="button" onClick={() => setMessagePageIndex(0)} disabled={clampedMessagePageIndex === 0}>首页</button>
                  <button type="button" onClick={() => setMessagePageIndex(Math.max(clampedMessagePageIndex - 1, 0))} disabled={clampedMessagePageIndex === 0}>上一页</button>
                  <span>第 {clampedMessagePageIndex + 1} / {messagePageCount} 页</span>
                  <button type="button" onClick={() => setMessagePageIndex(Math.min(clampedMessagePageIndex + 1, messagePageCount - 1))} disabled={clampedMessagePageIndex >= messagePageCount - 1}>下一页</button>
                  <button type="button" onClick={() => setMessagePageIndex(messagePageCount - 1)} disabled={clampedMessagePageIndex >= messagePageCount - 1}>末页</button>
                </div>
              ) : null}
              <p>当前发言者：{safeExcerpt(selected.turn_order[selected.current_turn_index] ?? "未设置")}</p>
              <p>知识安全状态：每个 NPC 只接收角色安全和会话安全上下文；NPC unknown facts 会被排除。</p>
              <button type="button" disabled={!selectedSceneId} onClick={onGenerateNext}>生成下一条回复</button>
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
    <TavernSafeSummaryPanel title="RP 记忆 / 关系摘要">
      <div className="tavern-card-meta">
        {["关系", "承诺", "偏好", "情绪", "边界", matureVisible ? "mature_only 已显式开启" : "mature_only 默认隐藏"].map((item) => <span key={item}>{item}</span>)}
      </div>
      <div className="tavern-filter-row">
        <input value={memorySearch} onChange={(event) => setMemorySearch(event.target.value)} placeholder="搜索安全记忆元数据" />
        <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)}>
          {typeOptions.map((type) => <option key={type} value={type}>{type}</option>)}
        </select>
        <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
          {[8, 16, 32].map((size) => <option key={size} value={size}>{size} 行</option>)}
        </select>
        {memorySearch !== debouncedMemorySearch ? <span className="tavern-chip">筛选中...</span> : null}
      </div>
      {rows.length === 0 ? <p className="muted">还没有安全 RP 记忆。</p> : filteredRows.length === 0 ? <p className="muted">没有 RP 记忆符合当前筛选。</p> : (
        <div data-windowed-rp-memory="true">
          <p className="muted">显示 {windowStart + 1}-{windowEnd} / {filteredRows.length} 条安全 RP 记忆。</p>
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
      <p className="muted">归档/删除需要确认；hidden/debug/mature-only memory 不会显示在普通视图。</p>
    </TavernSafeSummaryPanel>
  );
}

export function EmotionArcPanel({ messages = [] }: { messages?: TavernMessage[] }) {
  const recent = messages.slice(-4);
  return (
    <TavernSafeSummaryPanel title="情绪弧线">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="当前情绪" detail="primary emotion: calm / secondary: attentive / intensity: low / valence: neutral / arousal: low" />
        <MemorySummaryCard title="触发摘要" detail={recent.length ? recent.map((message) => `${message.speaker_type}:${message.message_id}`).join(", ") : "暂无近期安全触发引用。"} />
      </div>
      <details>
        <summary>创作备注（仅 authoring）</summary>
        <p className="muted">除非安全策略明确允许，否则 authoring notes 不会进入普通 Tavern prompt context。</p>
      </details>
    </TavernSafeSummaryPanel>
  );
}

export function RelationshipTonePanel({ characters = [], sessions = [], onPropose }: { characters?: TavernCharacter[]; sessions?: TavernSession[]; onPropose?: () => void }) {
  const pairs = sessions.flatMap((session) => session.character_ids.slice(0, 2).length >= 2 ? [{ a: session.character_ids[0], b: session.character_ids[1], source: "tavern memory" }] : []);
  return (
    <TavernSafeSummaryPanel title="关系语气">
      {pairs.length === 0 ? <p className="muted">还没有关系组合。请在会话或场景中加入多个角色。</p> : pairs.map((pair) => (
        <div key={`${pair.a}-${pair.b}`} className="memory-summary-card">
          <strong>{safeExcerpt(pair.a)} ↔ {safeExcerpt(pair.b)}</strong>
          <p>trust medium · affinity neutral · fear low · respect medium · tension low · resentment hidden by default · protectiveness unknown</p>
          <p className="muted">Source: {pair.source}. Hidden world relationships and mature/intimacy fields are not shown.</p>
        </div>
      ))}
      <p className="muted">已加载角色：{characters.length}。关系变化只会创建 {"Tavern -> World"} proposal。</p>
      <button type="button" onClick={onPropose}>创建 Tavern → World proposal</button>
    </TavernSafeSummaryPanel>
  );
}

export function SceneMoodPresetPanel({ presets, selectedPresetId, onSelect, onCreate }: { presets: TavernScenePreset[]; selectedPresetId?: string; onSelect?: (presetId: string) => void; onCreate?: () => void }) {
  return (
    <TavernSafeSummaryPanel title="场景氛围">
      <p>场景氛围只影响表达，不改变世界事实。Fade-to-black 策略默认保持安全。</p>
      <button type="button" onClick={onCreate}>创建本地预设</button>
      {presets.length === 0 ? <p className="muted">还没有场景氛围预设。</p> : presets.map((preset) => (
        <button key={preset.preset_id} type="button" className={`tavern-card ${preset.preset_id === selectedPresetId ? "selected-list-button" : ""}`} onClick={() => onSelect?.(preset.preset_id)}>
          <SceneMoodBadge preset={preset} />
          <span>节奏 {preset.pacing || "默认"} / 感官 {(preset.sensory_focus ?? []).join(", ") || "无"} / 情绪 {preset.emotional_tone || "neutral"}</span>
        </button>
      ))}
    </TavernSafeSummaryPanel>
  );
}

export function CharacterVoiceLabPanel({ character }: { character?: TavernCharacter | null }) {
  return (
    <TavernSafeSummaryPanel title="角色 Voice Lab">
      <div className="tavern-editor-grid">
        <label>语气<input readOnly value={character?.voice_profile_id ? "已关联文字 VoiceProfile" : "语气草稿"} /></label>
        <label>用词<input readOnly value="仅安全词汇和句式节奏" /></label>
        <label>口头禅<input readOnly value="在 VoiceProfile 编辑器中添加本地安全样例" /></label>
        <label>禁用表达<input readOnly value="private notes 不进入普通预览" /></label>
      </div>
      <p>仅文字声线。这里不调用 TTS、不自动调用真实 provider，private notes 不显示在普通预览。</p>
    </TavernSafeSummaryPanel>
  );
}

export function BoundaryMatureSettingsPanel({ preferences }: { preferences?: TavernPreferences | null }) {
  return (
    <TavernSafeSummaryPanel title="边界 / Mature 模块设置">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="Mature 默认关闭" detail="enabled=false by default；除非用户显式开启，否则可见设置保持关闭。" />
        <MemorySummaryCard title="导出 mature 内容" detail="默认 false；mature/private content 会从普通导出排除。" />
        <MemorySummaryCard title="未知年龄 / 未成年人阻断" detail="未知年龄或未成年人会阻断 mature scenes。" />
        <MemorySummaryCard title="需要 consent" detail="Consent 与 provider policy 必须通过后才能进入相应 rating。" />
      </div>
      <p className="muted">当前 mature 面板：{preferences?.mature_module_visible ? "已显式开启" : "关闭 / 隐藏"}。</p>
    </TavernSafeSummaryPanel>
  );
}

export function TavernPromptProviderPanel({
  promptProfileId,
  providerProfileId,
  modelId,
  providerSummary,
  missingProvider = false,
  useCase = "tavern_reply",
  onConfigureProvider
}: {
  promptProfileId?: string | null;
  providerProfileId?: string | null;
  modelId?: string | null;
  providerSummary?: string;
  missingProvider?: boolean;
  useCase?: string;
  onConfigureProvider?: () => void;
}) {
  return (
    <TavernSafeSummaryPanel title="Tavern 模型服务 / Prompt">
      <p>Prompt profile：{promptProfileId || "tavern default"}</p>
      <p>Provider profile：{providerProfileId || "Provider Gateway 安全路径"}</p>
      <p>当前模型：{modelId || "测试使用 mock / local_stub"}</p>
      <p>用途：{useCase}。Provider safety policy 与 mature routing 只显示安全摘要。</p>
      <p>{providerSummary || "API Key 不显示，raw prompt 隐藏，hidden facts 与 NPC secrets 被排除。"}</p>
      {missingProvider && onConfigureProvider ? <button type="button" onClick={onConfigureProvider}>配置模型服务</button> : null}
    </TavernSafeSummaryPanel>
  );
}

export function RPSafetyDashboardPanel({ report, onRun }: { report?: RPSafetyDashboardReport | null; onRun?: () => void }) {
  const categories = ["hidden facts", "NPC secrets / knowledge", "private persona", "mature memory", "provider safety routing", "world consistency", "proposal validation", "export safety"];
  return (
    <TavernSafeSummaryPanel title="RP Safety / 安全检查">
      <div className="safe-summary-grid">
        <MemorySummaryCard title="整体状态" detail={report ? `${report.overall_status}; blockers ${report.blocker_count}; warnings ${report.warning_count}` : "not_run"} />
        <MemorySummaryCard title="检查类别" detail={categories.join("; ")} />
      </div>
      <button type="button" onClick={onRun}>运行 RP Safety</button>
      {report?.issues.length ? report.issues.map((issue) => (
        <div key={`${issue.category}-${issue.safe_summary}`} className="memory-summary-card">
          <strong>{issue.severity} · {issue.category}</strong>
          <p>{safeExcerpt(issue.safe_summary)}</p>
          <p className="muted">Affected: {issue.affected_session_id || issue.affected_character_id || "project"} · Suggested action: {safeExcerpt(issue.suggested_action)}</p>
        </div>
      )) : <p className="muted">还没有 RP Safety 报告。运行本地检查以查看 hidden leak、NPC knowledge、mature boundary 与 provider routing。</p>}
    </TavernSafeSummaryPanel>
  );
}

export function TavernCrossModeSafetyPanel({ worldNpcs, exportPreview }: { worldNpcs?: WorldNpcSafeSummary[]; exportPreview?: TavernSessionExportPreview | null }) {
  return (
    <TavernSafeSummaryPanel title="跨模式 / 导出安全">
      <p>Tavern → World 仍然是 proposal / validation / dry-run / explicit confirm。Tavern → Novel 只创建过滤后的场景草稿。</p>
      <p>World NPC → Tavern 的 player_safe 模式会排除 NPC secrets 和未知事实。</p>
      <LinkedText title="安全 World NPC 引用" values={(worldNpcs ?? []).map((npc) => `${npc.display_name}:${npc.npc_id}`)} />
      <p>导出预览：{exportPreview ? `${exportPreview.session_count} 个会话，${exportPreview.message_count} 条安全消息，${exportPreview.excluded_items.length} 个排除项` : "未运行"}</p>
      <p>过滤策略：{(exportPreview?.filtering_policy ?? ["API key excluded", "hidden facts excluded", "NPC secrets excluded", "mature/private excluded by default", "debug data excluded"]).join("; ")}</p>
    </TavernSafeSummaryPanel>
  );
}
