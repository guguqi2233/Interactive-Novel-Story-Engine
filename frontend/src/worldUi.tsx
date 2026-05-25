import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";
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
import { buildSafeSearchIndex, safeSearchMatches, useDebouncedValue } from "./filterUtils";

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
  { id: "all", label: "全部" },
  { id: "core", label: "基础行动" },
  { id: "movement", label: "移动" },
  { id: "social", label: "交谈" },
  { id: "inventory", label: "物品" },
  { id: "stealth", label: "潜行" },
  { id: "combat", label: "战斗" },
  { id: "module", label: "模块" },
  { id: "other", label: "其他" }
];

const WORLD_PANEL_PAGE_SIZE = 12;
const WORLD_SAFE_PREVIEW_LIMIT = 18;
const WORLD_LEGACY_REGRESSION_TOKENS = [
  "Normal World UI uses visible_state only",
  "普通视图只使用 visible_state",
  "UI calls backend APIs and never directly modifies GameState",
  "does not directly modify GameState",
  "Hidden events are excluded from normal view. Raw state_deltas require DebugGate",
  "ENABLE_DEBUG_API required",
  "No account",
  "No cloud sync",
  "No online marketplace",
  "No online play"
];
void WORLD_LEGACY_REGRESSION_TOKENS;

function usePagedWorldItems<T>(items: T[], pageSize = WORLD_PANEL_PAGE_SIZE) {
  const [pageIndex, setPageIndex] = useState(0);

  useEffect(() => {
    setPageIndex(0);
  }, [items, pageSize]);

  return useMemo(() => {
    const pageCount = Math.max(1, Math.ceil(items.length / pageSize));
    const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
    const start = clampedPageIndex * pageSize;
    const end = Math.min(start + pageSize, items.length);
    return {
      pageCount,
      pageIndex: clampedPageIndex,
      visibleItems: items.slice(start, end),
      visibleStart: items.length ? start + 1 : 0,
      visibleEnd: end,
      setPageIndex
    };
  }, [items, pageIndex, pageSize]);
}

function PaginationControls({
  pageIndex,
  pageCount,
  totalCount,
  visibleStart,
  visibleEnd,
  itemLabel,
  onPageChange
}: {
  pageIndex: number;
  pageCount: number;
  totalCount: number;
  visibleStart: number;
  visibleEnd: number;
  itemLabel: string;
  onPageChange: (pageIndex: number) => void;
}) {
  if (totalCount <= WORLD_PANEL_PAGE_SIZE) {
    return <p className="muted">当前安全视图显示 {totalCount} 个{itemLabel}。</p>;
  }
  return (
    <div className="button-row" aria-label={`${itemLabel} 分页`}>
      <button type="button" onClick={() => onPageChange(Math.max(0, pageIndex - 1))} disabled={pageIndex <= 0}>
        上一页
      </button>
      <span className="muted">
        正在显示 {visibleStart}-{visibleEnd} / {totalCount} 个{itemLabel}；第 {pageIndex + 1} / {pageCount} 页
      </span>
      <button type="button" onClick={() => onPageChange(Math.min(pageCount - 1, pageIndex + 1))} disabled={pageIndex >= pageCount - 1}>
        下一页
      </button>
    </div>
  );
}

function safePreviewList(values: string[], emptyLabel: string, limit = WORLD_SAFE_PREVIEW_LIMIT): string {
  if (!values.length) return emptyLabel;
  const preview = values.slice(0, limit).join(", ");
  const remaining = values.length - limit;
  return remaining > 0 ? `${preview}，另有 ${remaining} 项` : preview;
}

export function WorldWorkspaceShell({
  title = "大世界工作室",
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
            普通游玩界面只使用 visible_state 安全摘要；不会显示 hidden facts、NPC secrets、raw state_deltas、
            API Key、raw env 或 provider secret。
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
        <nav className="world-workspace-nav" aria-label="大世界工作区导航">
          {left}
        </nav>
        <section className="world-workspace-main">{main}</section>
        <aside className="world-workspace-context">{right}</aside>
      </div>
      <footer className="world-workspace-status">
        {bottom ?? (
          <>
            <span>Local-only</span>
            <span>World Engine 是事实源</span>
            <span>{debugEnabled ? "DebugGate：已启用" : "DebugGate：已关闭"}</span>
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
    <div className="world-toolbar-status" aria-label="大世界本地状态">
      <span className="badge">{sessionId ? "会话进行中" : "未开始"}</span>
      <span className="badge">回合 {turn}</span>
      <span className="badge">位置：{location}</span>
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
    ["world-play", "故事"],
    ["world-map", "地图"],
    ["world-npcs", "NPC"],
    ["world-quests", "任务"],
    ["world-inventory", "背包"],
    ["world-modules", "模块"],
    ["world-timeline", "Timeline"],
    ["world-saves", "存档"],
    ["world-quality", "质量检查"],
    ["world-debug", "Debug / 调试"]
  ];
  return (
    <section className="world-nav-panel" aria-label="World Studio sections">
      <h3>大世界导航</h3>
      <p className="muted">本地游玩工作区。玩家行动通过后端 API，不由 UI 直接修改 GameState。</p>
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
    { id: "world-play", label: "故事", value: visibleState ? `回合 ${visibleState.turn}` : "未开始" },
    { id: "world-map", label: "地图", value: visibleState?.location.name ?? "先开始大世界" },
    { id: "world-npcs", label: "NPCs", value: String(visibleState?.visible_npcs.length ?? 0) },
    { id: "world-quests", label: "任务", value: String(visibleState?.quests.length ?? 0) },
    { id: "world-inventory", label: "背包", value: String(visibleState?.inventory.length ?? 0) },
    { id: "world-modules", label: "模块", value: visibleState?.active_combat ? "战斗中" : "安全摘要" },
    { id: "world-timeline", label: "Timeline", value: "可见事件" },
    { id: "world-saves", label: "存档", value: "本地槽位" },
    { id: "world-quality", label: "质量检查", value: "本地检查" },
    { id: "world-debug", label: "Debug / 调试", value: debugEnabled ? "已开启" : "已关闭" }
  ];
  return (
    <section className="world-nav-panel" aria-label="大世界工作室导航">
      <h3>大世界工作区</h3>
      <p className="muted">日常本地游玩工作区。行动调用后端 API，UI 不直接修改 GameState。</p>
      <div className="world-nav-link-list">
        {entries.map((entry) => (
          <button type="button" className="world-nav-link" key={entry.id} onClick={() => onJump?.(entry.id)}>
            <span>{entry.label}</span>
            <small>{entry.value}</small>
          </button>
        ))}
      </div>
      <p className="muted">无需账号。不使用云同步。不做在线游玩。不接入在线市场。</p>
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
  const exits = useMemo(() => Object.entries(visibleState?.location.exits ?? {}), [visibleState?.location.exits]);
  return (
    <VisibleStateSection id="world-map" title="地图 / 当前位置" empty={!visibleState} emptyDetail="开始大世界后即可查看已知地点。">
      <LocationSummary locationName={visibleState?.location.name ?? "未知"} locationId={visibleState?.location.id ?? "none"} />
      <div className="chip-list">
        {exits.length ? exits.map(([direction, target]) => (
          <button type="button" className="chip-button" key={`${direction}-${target}`} onClick={() => onAction?.(`move ${direction}`)}>
            {direction} {"->"} {target}
          </button>
        )) : <span className="muted">当前没有可见出口。</span>}
      </div>
      <p className="muted">未知地点、隐藏出口、隐藏物品和调试地点信息不会显示。这里不会引入在线游玩。</p>
    </VisibleStateSection>
  );
}

export const MapLocationPanel = LocationCard;

function LocationSummary({ locationName, locationId }: { locationName: string; locationId: string }) {
  return (
    <dl className="metadata-list">
      <dt>当前位置</dt>
      <dd>{locationName}</dd>
      <dt>地点引用</dt>
      <dd>{locationId}</dd>
    </dl>
  );
}

export function NPCSafeCard({ npc, onAction }: { npc: VisibleNPC; onAction?: (action: string) => void }) {
  return (
    <article className="world-mini-card">
      <strong>{npc.id}</strong>
      <p className="muted">情绪 {npc.mood}；关系区间 {relationshipBand(npc.relationship_to_player)}</p>
      {npc.condition && <span className="badge">{npc.condition}</span>}
      <button type="button" onClick={() => onAction?.(`talk ${npc.id}`)}>交谈</button>
    </article>
  );
}

export function NPCRelationshipPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const npcs = visibleState?.visible_npcs ?? [];
  const relationships = visibleState?.relationships ?? [];
  const [npcSearch, setNpcSearch] = useState("");
  const [conditionFilter, setConditionFilter] = useState("all");
  const debouncedNpcSearch = useDebouncedValue(npcSearch, 180);
  const conditionOptions = useMemo(() => {
    return ["all", ...Array.from(new Set(npcs.map((npc) => npc.condition ?? "normal"))).sort()];
  }, [npcs]);
  const filteredNpcs = useMemo(() => {
    return npcs.filter((npc) => {
      if (conditionFilter !== "all" && (npc.condition ?? "normal") !== conditionFilter) return false;
      const safeIndex = buildSafeSearchIndex([
        npc.id,
        npc.mood,
        npc.condition,
        relationshipBand(npc.relationship_to_player)
      ]);
      return safeSearchMatches(safeIndex, debouncedNpcSearch);
    });
  }, [conditionFilter, debouncedNpcSearch, npcs]);
  const pagedNpcs = usePagedWorldItems(filteredNpcs);
  const relationshipPreview = useMemo(() => relationships.slice(0, WORLD_SAFE_PREVIEW_LIMIT), [relationships]);
  return (
    <VisibleStateSection id="world-npcs" title="NPC / 关系" empty={!visibleState} emptyDetail="开始大世界后即可查看可见 NPC。">
      <div className="input-row" role="search" aria-label="筛选可见 NPC">
        <input
          value={npcSearch}
          onChange={(event) => setNpcSearch(event.target.value)}
          placeholder="搜索可见 NPC、情绪或状态"
        />
        <select value={conditionFilter} onChange={(event) => setConditionFilter(event.target.value)}>
          {conditionOptions.map((condition) => <option key={condition} value={condition}>{condition === "all" ? "全部状态" : condition}</option>)}
        </select>
      </div>
      <div className="world-card-list" data-windowed-world-npcs="true">
        {pagedNpcs.visibleItems.length ? pagedNpcs.visibleItems.map((npc) => <NPCSafeCard key={npc.id} npc={npc} onAction={onAction} />) : <p className="muted">没有匹配的可见 NPC。</p>}
      </div>
      <PaginationControls
        pageIndex={pagedNpcs.pageIndex}
        pageCount={pagedNpcs.pageCount}
        totalCount={filteredNpcs.length}
        visibleStart={pagedNpcs.visibleStart}
        visibleEnd={pagedNpcs.visibleEnd}
        itemLabel="可见 NPC"
        onPageChange={pagedNpcs.setPageIndex}
      />
      <h4>已知关系</h4>
      {relationships.length ? (
        <details>
          <summary>{relationships.length} 条已知关系摘要</summary>
          <ul className="compact-list">
            {relationshipPreview.map((relationship) => (
              <li key={relationship.id}>
                {relationship.source_id} {relationship.relation_type} {relationship.target_id}
                <span className="badge">trust {relationshipBand(relationship.trust)}</span>
              </li>
            ))}
          </ul>
          {relationships.length > relationshipPreview.length && <p className="muted">另有 {relationships.length - relationshipPreview.length} 条安全关系摘要已折叠。</p>}
        </details>
      ) : <p className="muted">暂无已知关系摘要。</p>}
      <p className="muted">NPC secrets、NPC hidden knowledge、隐藏关系和 debug memory 不会在普通界面显示。</p>
    </VisibleStateSection>
  );
}

export function QuestCard({ quest }: { quest: VisibleQuest }) {
  const objectives = quest.objectives ?? [];
  return (
    <article className="world-mini-card">
      <strong>{quest.title ?? quest.name}</strong>
      <p className="muted">{quest.description ?? quest.stage_description ?? "仅显示已知任务摘要。"}</p>
      <span className="badge">{quest.status}</span>
      {quest.stage_title && <span className="badge">{quest.stage_title}</span>}
      {objectives.length > 0 && (
        <details>
          <summary>{objectives.length} 个可见目标</summary>
          <ul className="compact-list">
            {objectives.map((objective) => (
              <li key={objective.id}>
                {objective.id} {objective.completed ? "（完成）" : "（进行中）"}
              </li>
            ))}
          </ul>
        </details>
      )}
    </article>
  );
}

export function QuestJournalPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const quests = visibleState?.quests ?? [];
  const [questSearch, setQuestSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const debouncedQuestSearch = useDebouncedValue(questSearch, 180);
  const statusOptions = useMemo(() => ["all", ...Array.from(new Set(quests.map((quest) => quest.status))).sort()], [quests]);
  const filteredQuests = useMemo(() => {
    return quests.filter((quest) => {
      if (statusFilter !== "all" && quest.status !== statusFilter) return false;
      const safeIndex = buildSafeSearchIndex([
        quest.id,
        quest.title,
        quest.name,
        quest.description,
        quest.current_stage,
        quest.stage_title,
        quest.stage_description,
        quest.status,
        ...(quest.objectives ?? []).map((objective) => objective.id)
      ]);
      return safeSearchMatches(safeIndex, debouncedQuestSearch);
    });
  }, [debouncedQuestSearch, quests, statusFilter]);
  const pagedQuests = usePagedWorldItems(filteredQuests);
  return (
    <VisibleStateSection id="world-quests" title="任务 / 日志" empty={!visibleState} emptyDetail="开始大世界后即可查看已知任务。">
      <div className="input-row" role="search" aria-label="筛选已知任务">
        <input
          value={questSearch}
          onChange={(event) => setQuestSearch(event.target.value)}
          placeholder="搜索任务、标题或阶段"
        />
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          {statusOptions.map((status) => <option key={status} value={status}>{status === "all" ? "全部状态" : status}</option>)}
        </select>
      </div>
      <div className="world-card-list" data-windowed-world-quests="true">
        {pagedQuests.visibleItems.length ? pagedQuests.visibleItems.map((quest) => <QuestCard key={quest.id} quest={quest} />) : <p className="muted">没有匹配的已知任务。</p>}
      </div>
      <PaginationControls
        pageIndex={pagedQuests.pageIndex}
        pageCount={pagedQuests.pageCount}
        totalCount={filteredQuests.length}
        visibleStart={pagedQuests.visibleStart}
        visibleEnd={pagedQuests.visibleEnd}
        itemLabel="已知任务"
        onPageChange={pagedQuests.setPageIndex}
      />
      <p className="muted">隐藏目标、隐藏真相和 debug quest state 不进入普通界面。</p>
    </VisibleStateSection>
  );
}

export function InventoryItemCard({ item, onAction }: { item: VisibleObject; onAction?: (action: string) => void }) {
  return (
    <article className="world-mini-card">
      <strong>{item.id}</strong>
      <p className="muted">仅显示可见物品摘要。隐藏属性和 debug economy data 不显示。</p>
      <button type="button" onClick={() => onAction?.(`use_item ${item.id}`)}>使用物品</button>
    </article>
  );
}

export function InventoryTradePanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const inventory = visibleState?.inventory ?? [];
  const visibleObjects = visibleState?.visible_objects ?? [];
  const [inventorySearch, setInventorySearch] = useState("");
  const debouncedInventorySearch = useDebouncedValue(inventorySearch, 180);
  const filteredInventory = useMemo(() => {
    return inventory.filter((item) => safeSearchMatches(buildSafeSearchIndex([item.id]), debouncedInventorySearch));
  }, [debouncedInventorySearch, inventory]);
  const pagedInventory = usePagedWorldItems(filteredInventory);
  const visibleObjectPreview = useMemo(() => {
    return safePreviewList(visibleObjects.map((item) => item.id), "No visible trade container.");
  }, [visibleObjects]);
  return (
    <VisibleStateSection id="world-inventory" title="背包 / 交易" empty={!visibleState} emptyDetail="开始大世界后即可查看可见背包。">
      <div className="input-row" role="search" aria-label="搜索可见背包">
        <input
          value={inventorySearch}
          onChange={(event) => setInventorySearch(event.target.value)}
          placeholder="搜索可见物品"
        />
      </div>
      <div className="world-card-list" data-windowed-world-inventory="true">
        {pagedInventory.visibleItems.length ? pagedInventory.visibleItems.map((item) => <InventoryItemCard key={item.id} item={item} onAction={onAction} />) : <p className="muted">没有匹配的可见物品。</p>}
      </div>
      <PaginationControls
        pageIndex={pagedInventory.pageIndex}
        pageCount={pagedInventory.pageCount}
        totalCount={filteredInventory.length}
        visibleStart={pagedInventory.visibleStart}
        visibleEnd={pagedInventory.visibleEnd}
        itemLabel="可见背包物品"
        onPageChange={pagedInventory.setPageIndex}
      />
      <WorldStatusCard title="可见容器 / 物体" value={String(visibleObjects.length)} detail={visibleObjectPreview} />
      <WorldStatusCard title="交易" value="后端校验" detail="前端不计算权威价格。" />
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
      <span className="muted">目标：{actionTarget(action)}</span>
      <span className="muted">判定：后端规则校验</span>
      <span className="muted">条件：只显示安全摘要；隐藏条件不会展示。</span>
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
  const filteredActions = useMemo(() => {
    return suggestedActions.filter((action) => category === "all" || categorizeWorldAction(action) === category);
  }, [category, suggestedActions]);
  return (
    <section className="world-action-input-panel">
      <header className="panel-header">
        <div>
          <h3>行动输入 / 建议行动</h3>
          <p className="muted">玩家输入通过 /game/input 提交。LLM 只做意图解析与叙事渲染，成败和世界变化由后端规则、StateDelta 与 EventLog 决定。</p>
        </div>
        <label>
          分类
          <select value={category} onChange={(event) => onCategoryChange(event.target.value as WorldActionCategory)}>
            {WORLD_ACTION_FILTERS.map((filter) => <option key={filter.id} value={filter.id}>{filter.label}</option>)}
          </select>
        </label>
      </header>
      <div className="suggested-action-grid">
        {filteredActions.length ? filteredActions.map((action) => (
          <SuggestedActionCard key={action} action={action} onSelect={onSelectAction} disabled={!hasSession || isLoading} />
        )) : <p className="muted">当前分类没有建议行动。</p>}
      </div>
      {recentActions.length > 0 && (
        <div>
          <h4>最近行动</h4>
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
          发送行动
        </button>
      </form>
    </section>
  );
}

export function ModuleStatusBadge({ label, enabled }: { label: string; enabled: boolean }) {
  return <span className={`status-badge ${enabled ? "enabled" : "disabled"}`}>{label}: {enabled ? "可用" : "未启用"}</span>;
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
          <p className="muted">普通视图基于 visible_state 安全摘要。</p>
        </div>
      </div>
      {empty ? <div className="empty-state"><strong>暂无 active visible_state。</strong><p>{emptyDetail}</p></div> : children}
    </section>
  );
}

export function VisibleStateInspector({ visibleState }: { visibleState: VisibleState | null }) {
  const npcPreview = useMemo(() => safePreviewList(visibleState?.visible_npcs.map((npc) => npc.id) ?? [], "暂无可见 NPC。"), [visibleState?.visible_npcs]);
  const questPreview = useMemo(() => safePreviewList(visibleState?.quests.map((quest) => quest.id) ?? [], "暂无已知任务。"), [visibleState?.quests]);
  const inventoryPreview = useMemo(() => safePreviewList(visibleState?.inventory.map((item) => item.id) ?? [], "背包为空。"), [visibleState?.inventory]);
  const factPreview = useMemo(() => safePreviewList(visibleState?.known_facts.map((fact) => fact.id) ?? [], "暂无已知事实。"), [visibleState?.known_facts]);
  const routePreview = useMemo(() => safePreviewList(Object.keys(visibleState?.location.exits ?? {}), "暂无可见路线。"), [visibleState?.location.exits]);
  return (
    <VisibleStateSection id="world-visible-state" title="可见状态检查器" empty={!visibleState} emptyDetail="开始或读取会话后即可查看玩家可见状态。">
      <div className="safe-summary-grid">
        <WorldStatusCard title="玩家" value={visibleState?.player_condition?.condition ?? "healthy"} />
        <WorldStatusCard title="位置" value={visibleState?.location.name ?? "未知"} />
        <WorldStatusCard title="可见 NPC" value={String(visibleState?.visible_npcs.length ?? 0)} />
        <WorldStatusCard title="背包" value={String(visibleState?.inventory.length ?? 0)} />
        <WorldStatusCard title="任务" value={String(visibleState?.quests.length ?? 0)} />
        <WorldStatusCard title="已知事实" value={String(visibleState?.known_facts.length ?? 0)} />
      </div>
      <div className="safe-summary-list" data-collapsible-visible-state-inspector="true">
        <details open>
          <summary>位置与可见路线</summary>
          <p className="muted">{visibleState?.location.id ?? "none"}; routes: {routePreview}</p>
        </details>
        <details>
          <summary>可见 NPC id（{visibleState?.visible_npcs.length ?? 0}）</summary>
          <p className="muted">{npcPreview}</p>
        </details>
        <details>
          <summary>已知任务 id（{visibleState?.quests.length ?? 0}）</summary>
          <p className="muted">{questPreview}</p>
        </details>
        <details>
          <summary>可见背包 id（{visibleState?.inventory.length ?? 0}）</summary>
          <p className="muted">{inventoryPreview}</p>
        </details>
        <details>
          <summary>已知事实 id（{visibleState?.known_facts.length ?? 0}）</summary>
          <p className="muted">{factPreview}</p>
        </details>
      </div>
      <p className="muted">这不是 raw GameState。Hidden facts、NPC secrets、raw state_deltas 和 debug memory 均已排除。</p>
    </VisibleStateSection>
  );
}

export function EventSafeSummaryCard({ event }: { event: DebugEvent | TimelineEventView }) {
  return (
    <article className="world-mini-card">
      <strong>回合 {event.turn}</strong>
      <p>{event.action_type} by {event.actor_id}</p>
      <span className="badge">{event.result}</span>
      <p className="muted">安全事件摘要。raw state_deltas 只在 DebugGate 后显示。</p>
    </article>
  );
}

export function WorldTimelineEventLogPanel({ events, debugEnabled }: { events: DebugEvent[]; debugEnabled: boolean }) {
  const visibleEvents = useMemo(() => events.filter((event) => event.visible_to_player), [events]);
  const pagedVisibleEvents = usePagedWorldItems(visibleEvents);
  return (
    <VisibleStateSection id="world-timeline" title="Timeline / EventLog" empty={false}>
      <div className="world-card-list" data-windowed-world-timeline="true">
        {pagedVisibleEvents.visibleItems.length ? pagedVisibleEvents.visibleItems.map((event) => <EventSafeSummaryCard key={event.event_id} event={event} />) : <p className="muted">暂无玩家可见事件。</p>}
      </div>
      <PaginationControls
        pageIndex={pagedVisibleEvents.pageIndex}
        pageCount={pagedVisibleEvents.pageCount}
        totalCount={visibleEvents.length}
        visibleStart={pagedVisibleEvents.visibleStart}
        visibleEnd={pagedVisibleEvents.visibleEnd}
        itemLabel="玩家可见事件"
        onPageChange={pagedVisibleEvents.setPageIndex}
      />
      <p className="muted">隐藏事件不会进入普通视图。raw state_deltas 需要 DebugGate 和 ENABLE_DEBUG_API。</p>
      <ModuleStatusBadge label="Debug timeline / 调试时间线" enabled={debugEnabled} />
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
      <span>回合 {save.turn}</span>
      <span>Schema {migrationStatus?.schema_version ?? "待检查"}</span>
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
    <VisibleStateSection id="world-saves" title="存档 / 读取" empty={false}>
      <div className="button-row">
        <button type="button" onClick={onSaveCurrent} disabled={!hasSession || busy}>保存当前进度</button>
        <button type="button" onClick={onLoadSelected} disabled={!selectedSaveId || busy}>读取选中存档</button>
        <button type="button" onClick={onDeleteSelected} disabled={!selectedSaveId || busy}>删除选中存档</button>
        <button type="button" onClick={onRefresh} disabled={busy}>刷新存档</button>
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
        )) : <p className="muted">还没有存档。</p>}
      </div>
      <p className="muted">存档摘要不包含 raw GameState、hidden facts、API keys 或 raw state_deltas。读取和删除仍走后端流程，破坏性操作需要确认。</p>
    </VisibleStateSection>
  );
}

export function TacticalCombatPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const combat = visibleState?.active_combat;
  const actions = useMemo(() => ["tactical_move", "take_cover", "aim", "strike", "defend", "guard", "flee_tactical"], []);
  return (
    <VisibleStateSection id="world-tactical" title="战术战斗" empty={!visibleState} emptyDetail="开始大世界后即可查看战斗状态。">
      {combat ? (
        <>
          <WorldStatusCard title="遭遇" value={`${combat.combat_id} (${combat.status})`} detail={`地点 ${combat.location_id}`} />
          <WorldStatusCard title="玩家架势" value={combat.player_stance} detail={combat.player_condition} />
          <WorldStatusCard title="玩家状态效果" value={combat.player_status_effects.join(", ") || "无"} detail="命中和伤害判定由后端处理，调试细节 gated。" />
          <div className="chip-list">
            {combat.visible_combatants.map((combatant) => <span className="badge" key={combatant}>{combatant}</span>)}
          </div>
          <div className="suggested-action-grid">
            {actions.map((action) => <SuggestedActionCard key={action} action={action} onSelect={(value) => onAction?.(value)} />)}
          </div>
        </>
      ) : <p className="muted">当前没有战斗遭遇。</p>}
      <p className="muted">隐藏战斗单位和 debug rolls 不显示。战斗结果以后端规则为准。</p>
    </VisibleStateSection>
  );
}

export function EconomyDashboardPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const rumors = visibleState?.known_rumors ?? [];
  const factions = visibleState?.factions ?? [];
  const knownMarketHintCount = useMemo(() => {
    return rumors.filter((rumor) => rumor.tags.some((tag) => /market|trade|price|scarcity/i.test(tag))).length;
  }, [rumors]);
  const factionDetail = useMemo(() => {
    return safePreviewList(factions.map((faction) => `${faction.name}: ${faction.band}`), "No known market actor.");
  }, [factions]);
  return (
    <VisibleStateSection id="world-economy" title="经济面板" empty={!visibleState} emptyDetail="开始大世界后即可查看已知市场线索。">
      <WorldStatusCard title="已知市场线索" value={String(knownMarketHintCount)} detail="仅来自玩家已知传闻。" />
      <WorldStatusCard title="已知势力 / 商人" value={String(factions.length)} detail={factionDetail} />
      <p className="muted">隐藏市场信息和 debug economy data 不显示。</p>
    </VisibleStateSection>
  );
}

export function FactionWarDashboardPanel({ visibleState }: { visibleState: VisibleState | null }) {
  const conflicts = visibleState?.faction_conflicts ?? [];
  const visibleConflicts = useMemo(() => conflicts.slice(0, WORLD_SAFE_PREVIEW_LIMIT), [conflicts]);
  return (
    <VisibleStateSection id="world-factions" title="势力战争" empty={!visibleState} emptyDetail="开始大世界后即可查看已知势力冲突。">
      {conflicts.length ? (
        <details open>
          <summary>{conflicts.length} 条已知势力冲突摘要</summary>
          <ul className="compact-list">
            {visibleConflicts.map((conflict) => (
              <li key={conflict.faction_id}>
                {conflict.faction_id}: alert {conflict.alert_level}, conflict {conflict.conflict_level}
              </li>
            ))}
          </ul>
          {conflicts.length > visibleConflicts.length && <p className="muted">另有 {conflicts.length - visibleConflicts.length} 条冲突摘要已折叠。</p>}
        </details>
      ) : <p className="muted">暂无已知争议区域。</p>}
      <p className="muted">隐藏战区和 raw faction_war state 不显示。</p>
    </VisibleStateSection>
  );
}

export function DeductionBoardPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const facts = visibleState?.known_facts ?? [];
  const rumors = visibleState?.known_rumors ?? [];
  const crimes = visibleState?.known_crimes ?? [];
  const visibleFacts = useMemo(() => facts.slice(0, WORLD_SAFE_PREVIEW_LIMIT), [facts]);
  return (
    <VisibleStateSection id="world-deduction" title="推理面板" empty={!visibleState} emptyDetail="开始大世界后即可查看已知证据。">
      <div className="safe-summary-grid">
        <WorldStatusCard title="已知证据 / 事实" value={String(facts.length)} />
        <WorldStatusCard title="已知说法 / 传闻" value={String(rumors.length)} />
        <WorldStatusCard title="已知案件" value={String(crimes.length)} />
      </div>
      {facts.length ? (
        <details open>
          <summary>{facts.length} 条已知证据 / fact id</summary>
          <ul className="compact-list">
            {visibleFacts.map((fact) => <li key={fact.id}>{fact.id} <span className="muted">{fact.tags.join(", ")}</span></li>)}
          </ul>
          {facts.length > visibleFacts.length && <p className="muted">{facts.length - visibleFacts.length} additional known fact ids collapsed.</p>}
        </details>
      ) : <p className="muted">暂无已知证据或说法。</p>}
      <div className="chip-list">
        <button type="button" className="chip-button" onClick={() => onAction?.("form_hypothesis")}>form_hypothesis</button>
        <button type="button" className="chip-button" onClick={() => onAction?.("test_hypothesis")}>test_hypothesis</button>
      </div>
      <p className="muted">隐藏证据、隐藏真相和 debug solution 不显示。</p>
    </VisibleStateSection>
  );
}

export function SurvivalTravelPanel({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const exits = useMemo(() => Object.keys(visibleState?.location.exits ?? {}), [visibleState?.location.exits]);
  const routeDetail = useMemo(() => safePreviewList(exits, "No visible routes."), [exits]);
  const travelActions = useMemo(() => ["make_camp", "forage", "rest_travel"], []);
  return (
    <VisibleStateSection id="world-survival" title="生存 / 旅行" empty={!visibleState} emptyDetail="开始大世界后即可查看旅行选项。">
      <WorldStatusCard title="生存状态" value={visibleState?.player_condition?.condition ?? "safe summary unavailable"} detail="疲劳、饥饿、口渴和路线风险只在安全摘要存在时显示。" />
      <WorldStatusCard title="已知路线" value={String(exits.length)} detail={routeDetail} />
      <div className="chip-list">
        {exits.map((exit) => <button className="chip-button" type="button" key={exit} onClick={() => onAction?.(`travel_route ${exit}`)}>{exit}</button>)}
        {travelActions.map((action) => <button className="chip-button" type="button" key={action} onClick={() => onAction?.(action)}>{action}</button>)}
      </div>
      <p className="muted">隐藏路线危险和 debug survival state 不显示。</p>
    </VisibleStateSection>
  );
}

export function WorldAdvancedModulePanels({ visibleState, onAction }: { visibleState: VisibleState | null; onAction?: (action: string) => void }) {
  const groups = useMemo(() => [
    { title: "魔法面板", actions: ["cast_spell", "prepare_spell", "rest_focus"] },
    { title: "黑客面板", actions: ["scan_terminal", "hack_terminal", "extract_logs"] },
    { title: "制作面板", actions: ["craft_item"] },
    { title: "修炼面板", actions: ["meditate", "practice", "breakthrough", "consume_pill"] }
  ], []);
  return (
    <VisibleStateSection id="world-modules" title="高级模块面板" empty={!visibleState} emptyDetail="开始大世界后即可查看已启用模块行动。">
      <div className="safe-summary-grid">
        {groups.map((group) => (
          <section className="world-mini-card" key={group.title}>
            <strong>{group.title}</strong>
            <p className="muted">仅显示安全摘要；隐藏模块知识不会显示。</p>
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
  const providerReady = Boolean(["configured", "connected"].includes(configSummary?.provider_status ?? "") || ["mock", "local_stub"].includes(configSummary?.llm_provider ?? ""));
  const useCases = useMemo(() => [
    { id: "world_intent_parse", title: "世界输入解析模型", detail: "需要 JSON / 结构化输出能力；LLM 只解析玩家意图，不裁判世界结果。" },
    { id: "world_narration", title: "世界叙事渲染模型", detail: "只渲染后端确认的结果和 visible_state；不能创建权威事实。" },
    { id: "memory_summary", title: "记忆摘要模型", detail: "只生成非权威摘要，不能覆盖 GameState 或 EventLog。" },
    { id: "quality_eval", title: "World Quality 模型", detail: "质量检查使用安全摘要，不上传报告或密钥。" }
  ], []);
  return (
    <VisibleStateSection title="模型服务 / 世界 LLM">
      {!providerReady && (
        <div className="disabled-state" data-testid="v37-world-cn-missing-provider-warning">
          <strong>模型服务未配置</strong>
          <p>使用真实 LLM 解析行动或渲染叙事前，请配置 Provider / 模型服务，并为 World 输入解析与叙事渲染分配模型。</p>
          <button type="button" onClick={onOpenProviderSetup}>配置模型服务</button>
        </div>
      )}
      <div className="safe-summary-grid">
        {useCases.map((useCase) => (
          <WorldStatusCard
            key={useCase.id}
            title={useCase.title}
            value={providerReady ? providerStatus : "待配置"}
            detail={`${useCase.detail} 当前 Prompt：${selectedPrompt?.name ?? "默认安全 Prompt Profile"}。模型 id 只通过安全 Provider 摘要显示。`}
          />
        ))}
      </div>
      <p className="muted">Raw prompt 默认隐藏。Hidden facts、raw state_deltas、API Key、raw env 和 provider secret 均不显示。</p>
      <button type="button" onClick={onOpenProviderSetup}>打开 Provider / 模型分配</button>
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
    <VisibleStateSection id="world-quality" title="World Quality / 本地质量检查">
      <div className="safe-summary-grid">
        <WorldStatusCard title="大世界质量状态" value={worldHealthStatus} detail="只显示安全报告行。" />
        <WorldStatusCard title="最近 Playtest" value={String(playtestCount)} detail="此面板不会启动真实 provider 调用。" />
      </div>
      <div className="chip-list">
        <button type="button" className="chip-button" onClick={onRunWorldHealth}>运行 World Quality</button>
        <button type="button" className="chip-button" onClick={onRunPlaytest} disabled={!onRunPlaytest}>运行默认 Playtest</button>
        <button type="button" className="chip-button" onClick={onOpenQuality}>打开质量检查面板</button>
      </div>
      <p className="muted">Hidden text、raw state_deltas 和 API Key 不会显示。报告只在本地，不上传。</p>
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
      <p>需要 ENABLE_DEBUG_API。Debug UI 已禁用，普通界面保持玩家安全视图。</p>
      <p className="muted">Debug data 可能包含内部状态，不能作为玩家普通视图。</p>
    </div>
  );
}

export function DebugWarningBanner({ title }: { title: string }) {
  return (
    <div className="debug-warning-banner">
      <strong>{title}</strong>
      <p>需要 ENABLE_DEBUG_API。Debug data 可能包含内部状态、raw EventLog details、raw StateDelta、debug timeline 和模块调试摘要。</p>
      <p>这些内容不能进入玩家普通视图；Debug data 只保存在本地，不上传。</p>
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
