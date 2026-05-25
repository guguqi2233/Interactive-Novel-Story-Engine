import { ReactNode, useEffect, useMemo, useState } from "react";
import { NovelChapter, NovelDraftSnapshot, NovelManuscript, NovelScene, WritingSessionState } from "./api";
import { buildSafeSearchIndex, safeSearchMatches, useDebouncedValue } from "./filterUtils";
import { countWordsFast } from "./textUtils";

export type NovelIssue = {
  severity: string;
  code: string;
  message: string;
  category?: string;
  ref_type?: string;
  ref_id?: string;
  affected_label?: string;
  safe_detail?: string;
  suggested_action?: string;
};

export type NovelSearchResult = {
  result_type: string;
  result_id: string;
  title: string;
  status?: string;
  safe_summary?: string;
};

function safeExcerpt(text?: string | null, max = 160): string {
  const value = (text ?? "").replace(/(api[_\s-]?key|authorization|hidden[_\s-]?fact|npc[_\s-]?secret|private[_\s-]?note|state[_\s-]?delta|raw[_\s-]?prompt)\s*[:=]\s*[^\n,;]+/gi, "$1=[redacted]");
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

export function NovelStatusBadge({ status }: { status?: string | null }) {
  const value = status || "draft";
  return <span className={`novel-status-badge novel-status-${value}`}>{value}</span>;
}

export function WordCountBadge({ text, count }: { text?: string | null; count?: number }) {
  const resolvedCount = useMemo(() => count ?? countWordsFast(text), [count, text]);
  return <span className="word-count-badge">{resolvedCount} 字</span>;
}

export function LinkedRefList({ title, refs }: { title: string; refs?: string[] }) {
  const safeRefs = (refs ?? []).filter(Boolean);
  return (
    <div className="linked-ref-list">
      <strong>{title}</strong>
      {safeRefs.length === 0 ? <span className="muted">无</span> : safeRefs.map((ref) => <span key={ref}>{ref}</span>)}
    </div>
  );
}

function uniqueRefs(values: Array<string | null | undefined>): string[] {
  return Array.from(new Set(values.filter(Boolean) as string[]));
}

function sceneTags(scene: NovelScene): string[] {
  return [
    scene.status || "draft",
    scene.pov_character_id ? `pov:${scene.pov_character_id}` : "",
    scene.location_ref ? `location:${scene.location_ref}` : "",
    ...(scene.linked_character_ids ?? []).map((id) => `character:${id}`)
  ].filter(Boolean);
}

export function ManuscriptCard({ manuscript, selected, onSelect }: { manuscript: NovelManuscript; selected?: boolean; onSelect?: () => void }) {
  return (
    <button type="button" className={`novel-card manuscript-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <div>
        <h4>{manuscript.title}</h4>
        <p className="muted">{safeExcerpt(manuscript.description) || "本地稿件草稿。"}</p>
      </div>
      <div className="novel-card-meta">
        <span>{manuscript.chapter_refs?.length ?? 0} 个关联章节</span>
        <span>{manuscript.genre_tags?.join(", ") || "未标记"}</span>
      </div>
    </button>
  );
}

export function ChapterCard({ chapter, selected, onSelect }: { chapter: NovelChapter; selected?: boolean; onSelect?: () => void }) {
  return (
    <button type="button" className={`novel-card chapter-card ${selected ? "selected-list-button" : ""}`} onClick={onSelect}>
      <div className="novel-card-title-row">
        <strong>{chapter.order_index + 1}. {chapter.title}</strong>
        <NovelStatusBadge status={chapter.status} />
      </div>
      <p className="muted">{safeExcerpt(chapter.summary) || "暂无章节摘要。"}</p>
      <div className="novel-card-meta">
        <WordCountBadge text={chapter.draft_text} />
        <span>{chapter.scene_refs?.length ?? 0} 个场景</span>
      </div>
    </button>
  );
}

export function SceneCard({ scene, onOpen }: { scene: NovelScene; onOpen?: () => void }) {
  return (
    <button type="button" className="novel-card scene-card" onClick={onOpen}>
      <div className="novel-card-title-row">
        <strong>{scene.title}</strong>
        <NovelStatusBadge status={scene.status} />
      </div>
      <p className="muted">{safeExcerpt(scene.summary) || "暂无场景摘要。"}</p>
      <div className="novel-card-meta">
        <span>章节 {scene.chapter_id}</span>
        <WordCountBadge text={scene.draft_text} />
      </div>
    </button>
  );
}

export function OutlineNodeView({ node, depth = 0 }: { node: { node_id: string; node_type: string; title: string; summary?: string; status?: string; children?: unknown[] }; depth?: number }) {
  return (
    <div className="outline-node-view" style={{ marginLeft: `${depth * 12}px` }}>
      <span className="outline-node-type">{node.node_type}</span>
      <strong>{node.title}</strong>
      <NovelStatusBadge status={node.status} />
      {node.summary && <p className="muted">{safeExcerpt(node.summary)}</p>}
    </div>
  );
}

export function NovelSafeSummaryPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <aside className="novel-safe-summary-panel">
      <h4>{title}</h4>
      {children}
      <p className="muted">Novel normal UI 不显示 API Key、hidden facts、private notes、raw prompts 和 raw state_deltas。</p>
    </aside>
  );
}

export function NovelToolbar({ title, actions, meta }: { title: string; actions?: ReactNode; meta?: ReactNode }) {
  return (
    <div className="novel-toolbar">
      <div>
        <h4>{title}</h4>
        {meta}
      </div>
      <div className="button-row">{actions}</div>
    </div>
  );
}

export function DraftSaveStatus({ dirty, saving, message }: { dirty?: boolean; saving?: boolean; message?: string }) {
  return (
    <span className={`draft-save-status ${dirty ? "dirty" : "clean"}`}>
      {saving ? "保存中..." : dirty ? "有未保存修改" : message || "已本地保存"}
    </span>
  );
}

export function NovelWorkspaceShell({
  navigation,
  main,
  context,
  status
}: {
  navigation: ReactNode;
  main: ReactNode;
  context: ReactNode;
  status: ReactNode;
}) {
  return (
    <section className="novel-workspace-shell">
      <nav className="novel-workspace-nav">{navigation}</nav>
      <main className="novel-workspace-main">{main}</main>
      <aside className="novel-workspace-context">{context}</aside>
      <footer className="novel-workspace-status">{status}</footer>
    </section>
  );
}

export function ManuscriptDashboard({ manuscripts, chapters, scenes }: { manuscripts: NovelManuscript[]; chapters: NovelChapter[]; scenes: NovelScene[] }) {
  const words = useMemo(
    () => chapters.reduce((total, chapter) => total + countWordsFast(chapter.draft_text), 0) + scenes.reduce((total, scene) => total + countWordsFast(scene.draft_text), 0),
    [chapters, scenes]
  );
  return (
    <div className="novel-dashboard-grid">
      <NovelMetric title="稿件" value={manuscripts.length} />
      <NovelMetric title="章节" value={chapters.length} />
      <NovelMetric title="场景" value={scenes.length} />
      <NovelMetric title="总字数" value={words} />
    </div>
  );
}

function NovelMetric({ title, value }: { title: string; value: number | string }) {
  return <div className="novel-metric"><span>{title}</span><strong>{value}</strong></div>;
}

export function OutlineTreePro({
  chapters = [],
  scenes = [],
  selectedChapterId,
  onSelectChapter
}: {
  chapters?: NovelChapter[];
  scenes?: NovelScene[];
  selectedChapterId?: string;
  onSelectChapter?: (chapterId: string) => void;
}) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const orderedChapters = useMemo(() => [...chapters].sort((left, right) => left.order_index - right.order_index), [chapters]);
  const scenesByChapterId = useMemo(() => {
    const grouped = new Map<string, NovelScene[]>();
    for (const scene of scenes) {
      const list = grouped.get(scene.chapter_id) ?? [];
      list.push(scene);
      grouped.set(scene.chapter_id, list);
    }
    return grouped;
  }, [scenes]);

  if (orderedChapters.length === 0) {
    return (
      <NovelSafeSummaryPanel title="大纲树">
        <p>还没有大纲节点。添加章节后即可开始整理本地稿件结构。</p>
      </NovelSafeSummaryPanel>
    );
  }

  return (
    <NovelSafeSummaryPanel title="大纲树">
      <div className="outline-tree-pro">
        {orderedChapters.map((chapter, index) => {
          const childScenes = scenesByChapterId.get(chapter.chapter_id) ?? [];
          const isCollapsed = collapsed.has(chapter.chapter_id);
          const missing = [
            !chapter.summary ? "摘要" : "",
            childScenes.length === 0 ? "场景" : ""
          ].filter(Boolean);
          return (
            <div key={chapter.chapter_id} className={`outline-tree-node ${chapter.chapter_id === selectedChapterId ? "selected" : ""}`}>
              <button type="button" className="outline-tree-row" onClick={() => onSelectChapter?.(chapter.chapter_id)}>
                <span className="outline-node-type">章节</span>
                <strong>{index + 1}. {safeExcerpt(chapter.title)}</strong>
                <NovelStatusBadge status={chapter.status} />
                <WordCountBadge text={chapter.draft_text} />
              </button>
              <div className="novel-card-meta">
                <button
                  type="button"
                  onClick={() => {
                    const next = new Set(collapsed);
                    if (isCollapsed) next.delete(chapter.chapter_id);
                    else next.add(chapter.chapter_id);
                    setCollapsed(next);
                  }}
                >
                  {isCollapsed ? "展开" : "折叠"}
                </button>
                <button type="button" disabled title="重排需通过大纲 API 校验后执行。">移动</button>
                <span>{childScenes.length} 个场景</span>
                {missing.length > 0 && <span className="novel-warning-chip">缺少 {missing.join(", ")}</span>}
              </div>
              {!isCollapsed && (
                <div className="outline-tree-children">
                  {childScenes.length === 0 ? <p className="muted">还没有关联场景卡。</p> : childScenes.map((scene) => (
                    <OutlineNodeView
                      key={scene.scene_id}
                      depth={1}
                      node={{
                        node_id: scene.scene_id,
                        node_type: "场景",
                        title: scene.title,
                        summary: scene.summary,
                        status: scene.status
                      }}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </NovelSafeSummaryPanel>
  );
}

export function ChapterEditorPro({ children }: { children: ReactNode }) {
  return <div className="chapter-editor-pro">{children}</div>;
}

export function ChapterListPro({
  chapters,
  selectedChapterId,
  onSelectChapter
}: {
  chapters: NovelChapter[];
  selectedChapterId?: string;
  onSelectChapter: (chapter: NovelChapter) => void;
}) {
  const [pageSize, setPageSize] = useState(25);
  const [pageIndex, setPageIndex] = useState(0);
  const orderedChapters = useMemo(() => [...chapters].sort((left, right) => left.order_index - right.order_index), [chapters]);
  const pageCount = Math.max(1, Math.ceil(orderedChapters.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, orderedChapters.length);
  const visibleChapters = orderedChapters.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [chapters.length, pageSize]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  if (chapters.length === 0) {
    return <div className="novel-card-list"><p className="muted">还没有章节</p></div>;
  }

  return (
    <div className="novel-card-list" data-windowed-novel-chapters="true">
      <div className="novel-card-meta">
        <span>显示 {windowStart + 1}-{windowEnd} / {orderedChapters.length} 个章节</span>
        <label>
          每页
          <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
            {[10, 25, 50].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
      </div>
      {visibleChapters.map((chapter) => (
        <ChapterCard
          key={chapter.chapter_id}
          chapter={chapter}
          selected={chapter.chapter_id === selectedChapterId}
          onSelect={() => onSelectChapter(chapter)}
        />
      ))}
      {orderedChapters.length > pageSize ? (
        <div className="pagination-controls" aria-label="Novel 章节分页">
          <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>首页</button>
          <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>上一页</button>
          <span>第 {clampedPageIndex + 1} / {pageCount} 页</span>
          <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>下一页</button>
          <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>末页</button>
        </div>
      ) : null}
    </div>
  );
}

export function SceneCardsBoard({ scenes }: { scenes: NovelScene[] }) {
  const [filter, setFilter] = useState("");
  const debouncedFilter = useDebouncedValue(filter, 180);
  const [status, setStatus] = useState("all");
  const [pageSize, setPageSize] = useState(24);
  const [pageIndex, setPageIndex] = useState(0);
  const sceneSearchIndexById = useMemo(
    () =>
      new Map(
        scenes.map((scene) => [
          scene.scene_id,
          buildSafeSearchIndex([
            scene.title,
            scene.summary,
            scene.status,
            scene.pov_character_id,
            scene.location_ref,
            ...(scene.linked_character_ids ?? []),
            ...(scene.linked_world_event_ids ?? []),
            ...sceneTags(scene)
          ])
        ])
      ),
    [scenes]
  );
  const filtered = useMemo(
    () =>
      scenes.filter((scene) => {
        const matchesQuery = !debouncedFilter || safeSearchMatches(sceneSearchIndexById.get(scene.scene_id) ?? "", debouncedFilter);
        return matchesQuery && (status === "all" || (scene.status || "draft") === status);
      }),
    [debouncedFilter, sceneSearchIndexById, scenes, status]
  );
  const statuses = ["all", ...uniqueRefs(scenes.map((scene) => scene.status || "draft"))];
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, filtered.length);
  const visibleScenes = filtered.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [debouncedFilter, pageSize, scenes.length, status]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  return (
    <div className="stack">
      <NovelToolbar
        title="场景卡片"
        meta={<span className="muted">POV、地点、人物、状态、标签、字数和剧情引用都只属于 Novel 草稿。</span>}
        actions={(
          <>
            <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="筛选场景、标签、POV、地点" />
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statuses.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
              {[12, 24, 48].map((size) => <option key={size} value={size}>{size} 张卡片</option>)}
            </select>
            {filter !== debouncedFilter ? <span className="novel-chip">筛选中...</span> : null}
          </>
        )}
      />
      {filtered.length === 0 ? <p className="muted">没有匹配的场景。</p> : (
        <>
        <p className="muted">显示 {windowStart + 1}-{windowEnd} / {filtered.length} 个筛选后的场景。</p>
        <div className="scene-cards-board" data-windowed-novel-scenes="true">
          {visibleScenes.map((scene) => (
            <div key={scene.scene_id} className="scene-card-pro">
              <SceneCard scene={scene} />
              <div className="novel-card-meta">
                <span>POV {scene.pov_character_id || "未设置"}</span>
                <span>地点 {scene.location_ref || "未设置"}</span>
                <span>剧情 {scene.linked_world_event_ids?.[0] || "未关联"}</span>
              </div>
              <div className="novel-chip-row">
                {sceneTags(scene).map((tag) => <span key={tag} className="novel-chip">{safeExcerpt(tag, 40)}</span>)}
              </div>
            </div>
          ))}
        </div>
        {filtered.length > pageSize ? (
          <div className="pagination-controls" aria-label="Novel 场景分页">
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

export function CharacterArcPanel({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const characterSummaries = useMemo(() => {
    const characterIds = uniqueRefs([
      ...chapters.flatMap((chapter) => chapter.linked_character_ids ?? []),
      ...scenes.flatMap((scene) => scene.linked_character_ids ?? []),
      ...scenes.map((scene) => scene.pov_character_id)
    ]);
    return characterIds.map((characterId) => {
      const linkedScenes = scenes.filter((scene) => scene.pov_character_id === characterId || scene.linked_character_ids?.includes(characterId));
      const linkedChapters = chapters.filter((chapter) => chapter.linked_character_ids?.includes(characterId) || linkedScenes.some((scene) => scene.chapter_id === chapter.chapter_id));
      const stage = linkedScenes.length >= 3 ? "turning point ready" : linkedScenes.length > 0 ? "setup" : "unlinked";
      return { characterId, linkedChapters, linkedScenes, stage };
    });
  }, [chapters, scenes]);
  return (
    <NovelSafeSummaryPanel title="人物弧线">
      {characterSummaries.length === 0 ? <p>还没有关联人物。给章节或场景添加人物引用后即可追踪人物弧线。</p> : characterSummaries.map((summary) => (
          <div key={summary.characterId} className="novel-card compact">
            <div className="novel-card-title-row">
              <strong>{safeExcerpt(summary.characterId)}</strong>
              <NovelStatusBadge status={summary.stage} />
            </div>
            <p className="muted">动机和冲突说明仍是创作材料；转折点从关联的 safe scenes 推断。</p>
            <LinkedRefList title="关联章节" refs={summary.linkedChapters.map((chapter) => chapter.chapter_id)} />
            <LinkedRefList title="转折点" refs={summary.linkedScenes.slice(0, 4).map((scene) => scene.scene_id)} />
          </div>
        ))}
    </NovelSafeSummaryPanel>
  );
}

export function PlotForeshadowingBoard({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const linkedWorldEvents = useMemo(() => uniqueRefs(scenes.flatMap((scene) => scene.linked_world_event_ids ?? [])), [scenes]);
  const unresolvedScenes = useMemo(() => scenes.filter((scene) => !scene.summary || (scene.status || "draft") !== "complete"), [scenes]);
  return (
    <NovelSafeSummaryPanel title="剧情线 / 伏笔">
      <div className="novel-dashboard-grid">
        <NovelMetric title="剧情引用" value={linkedWorldEvents.length} />
        <NovelMetric title="未完成场景" value={unresolvedScenes.length} />
        <NovelMetric title="章节" value={chapters.length} />
      </div>
      {linkedWorldEvents.length === 0 ? <p className="muted">还没有剧情线引用。</p> : <LinkedRefList title="剧情线 / world refs" refs={linkedWorldEvents} />}
      {unresolvedScenes.slice(0, 5).map((scene) => (
        <p key={scene.scene_id}><strong>{safeExcerpt(scene.title)}</strong>：铺垫/回收状态需要检查。normal view 会隐藏敏感真相引用。</p>
      ))}
    </NovelSafeSummaryPanel>
  );
}

export function TimelineLinkPanel({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const timelineRefs = useMemo(
    () =>
      uniqueRefs([
        ...chapters.flatMap((chapter) => chapter.linked_timeline_event_ids ?? []),
        ...scenes.flatMap((scene) => scene.timeline_event_refs ?? []),
        ...scenes.flatMap((scene) => scene.linked_world_event_ids ?? [])
      ]),
    [chapters, scenes]
  );
  return (
    <NovelSafeSummaryPanel title="时间线链接">
      {timelineRefs.length === 0 ? <p>还没有 safe timeline refs。</p> : <LinkedRefList title="安全时间线 / world event refs" refs={timelineRefs} />}
      <p>时间线引用只用于参考；Novel UI 不能写入 World EventLog 或 GameState。</p>
    </NovelSafeSummaryPanel>
  );
}

export function WorldBibleSidebar({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const factRefs = useMemo(
    () =>
      uniqueRefs([
        ...chapters.flatMap((chapter) => chapter.linked_fact_ids ?? []),
        ...scenes.flatMap((scene) => scene.linked_fact_ids ?? [])
      ]),
    [chapters, scenes]
  );
  return (
    <NovelSafeSummaryPanel title="世界资料侧栏">
      {factRefs.length === 0 ? <p>还没有 novel-safe World Bible refs。</p> : <LinkedRefList title="novel-safe fact refs" refs={factRefs} />}
      <p>World facts 只作为写作参考；hidden facts 和 NPC secrets 不进入 Novel normal UI。</p>
    </NovelSafeSummaryPanel>
  );
}

export function NovelPromptProviderPanel({
  promptProfileId,
  providerSummary,
  currentModel,
  missingProvider,
  onConfigureProvider
}: {
  promptProfileId?: string | null;
  providerSummary?: string;
  currentModel?: string;
  missingProvider?: boolean;
  onConfigureProvider?: () => void;
}) {
  return (
    <NovelSafeSummaryPanel title="Novel 模型服务 / Provider">
      <p>Prompt profile：{promptProfileId || "项目默认"}</p>
      <p>当前模型：{currentModel || "未分配 Novel 模型"}</p>
      <p>{providerSummary || "仅显示 safe summary；API Key 不会显示。"}</p>
      <p>用途：novel_draft / novel_rewrite / cheap_summary。</p>
      {missingProvider && (
        <div className="notice-panel">
          <strong>需要配置模型服务</strong>
          <p>使用真实 LLM 生成、改写或摘要前，请先配置模型服务并分配 Novel 模型。</p>
          {onConfigureProvider && <button type="button" onClick={onConfigureProvider}>配置模型服务</button>}
        </div>
      )}
    </NovelSafeSummaryPanel>
  );
}

export function NovelExportWizard({ onExportMarkdown, onExportTxt }: { onExportMarkdown: () => void; onExportTxt: () => void }) {
  return (
    <NovelSafeSummaryPanel title="Novel 导出">
      <p>Markdown / TXT 导出默认过滤 authoring notes、hidden refs、mature/private、debug data 和 API Key。</p>
      <div className="button-row">
        <button type="button" onClick={onExportMarkdown}>导出 Markdown</button>
        <button type="button" onClick={onExportTxt}>导出 TXT</button>
      </div>
    </NovelSafeSummaryPanel>
  );
}

export function NovelQualityDashboard({ issues, onRun }: { issues: NovelIssue[]; onRun?: () => void }) {
  return (
    <NovelSafeSummaryPanel title="Novel Quality / 质量检查">
      <div className="button-row">
        {onRun && <button type="button" onClick={onRun}>运行 Novel Quality</button>}
      </div>
      {issues.length === 0 ? <p>暂无问题。导出前可运行本地 Novel Quality 检查。</p> : (
        <div className="novel-quality-list">
          {issues.map((issue) => (
            <div key={`${issue.code}-${issue.ref_id ?? issue.message}`} className={`novel-quality-row severity-${issue.severity}`}>
              <div className="novel-card-title-row">
                <strong>{safeExcerpt(issue.severity)}</strong>
                <span>{safeExcerpt(issue.category || issue.code)}</span>
              </div>
              <p>{safeExcerpt(issue.safe_detail || issue.message)}</p>
              <p className="muted">影响对象：{safeExcerpt(issue.affected_label || [issue.ref_type, issue.ref_id].filter(Boolean).join(":") || "稿件")}</p>
              <p className="muted">建议：{safeExcerpt(issue.suggested_action || "修订相关草稿后重新运行本地质量检查。")}</p>
            </div>
          ))}
        </div>
      )}
    </NovelSafeSummaryPanel>
  );
}

export function NovelSearchFilterBar({
  value,
  status,
  tag,
  onChange,
  onStatusChange,
  onTagChange
}: {
  value: string;
  status?: string;
  tag?: string;
  onChange: (value: string) => void;
  onStatusChange?: (value: string) => void;
  onTagChange?: (value: string) => void;
}) {
  const [draftValue, setDraftValue] = useState(value);
  const [draftTag, setDraftTag] = useState(tag || "");
  const debouncedValue = useDebouncedValue(draftValue, 220);
  const debouncedTag = useDebouncedValue(draftTag, 220);

  useEffect(() => {
    setDraftValue(value);
  }, [value]);

  useEffect(() => {
    setDraftTag(tag || "");
  }, [tag]);

  useEffect(() => {
    if (debouncedValue !== value) {
      onChange(debouncedValue);
    }
  }, [debouncedValue, onChange, value]);

  useEffect(() => {
    const currentTag = tag || "";
    if (onTagChange && debouncedTag !== currentTag) {
      onTagChange(debouncedTag);
    }
  }, [debouncedTag, onTagChange, tag]);

  return (
    <div className="novel-search-bar">
      <label>
        搜索 Novel
        <input value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder="搜索章节、场景、剧情线" />
      </label>
      <label>
        状态
        <select value={status || ""} onChange={(event) => onStatusChange?.(event.target.value)}>
          <option value="">全部</option>
          <option value="draft">草稿</option>
          <option value="revision">修订</option>
          <option value="complete">完成</option>
        </select>
      </label>
      <label>
        标签
        <input value={draftTag} onChange={(event) => setDraftTag(event.target.value)} placeholder="人物、剧情、地点" />
      </label>
      {draftValue !== debouncedValue || draftTag !== debouncedTag ? <span className="novel-chip">筛选中...</span> : null}
    </div>
  );
}

export function DraftVersionPanel({ snapshots, onCompare }: { snapshots: NovelDraftSnapshot[]; onCompare: (snapshotId: string) => void }) {
  const [collapsed, setCollapsed] = useState(false);
  const [pageSize, setPageSize] = useState(10);
  const [pageIndex, setPageIndex] = useState(0);
  const orderedSnapshots = useMemo(
    () => [...snapshots].sort((left, right) => String(right.created_at ?? "").localeCompare(String(left.created_at ?? ""))),
    [snapshots]
  );
  const pageCount = Math.max(1, Math.ceil(orderedSnapshots.length / pageSize));
  const clampedPageIndex = Math.min(pageIndex, pageCount - 1);
  const windowStart = clampedPageIndex * pageSize;
  const windowEnd = Math.min(windowStart + pageSize, orderedSnapshots.length);
  const visibleSnapshots = collapsed ? [] : orderedSnapshots.slice(windowStart, windowEnd);

  useEffect(() => {
    setPageIndex(0);
  }, [pageSize, snapshots.length]);

  useEffect(() => {
    if (pageIndex > pageCount - 1) {
      setPageIndex(pageCount - 1);
    }
  }, [pageCount, pageIndex]);

  return (
    <NovelSafeSummaryPanel title="草稿版本对比">
      <div className="novel-card-meta">
        <button type="button" onClick={() => setCollapsed((value) => !value)}>{collapsed ? "显示快照" : "折叠快照"}</button>
        <span>{orderedSnapshots.length} 个本地快照</span>
        <label>
          每页
          <select value={pageSize} onChange={(event) => setPageSize(Number(event.target.value))}>
            {[5, 10, 25].map((size) => <option key={size} value={size}>{size}</option>)}
          </select>
        </label>
      </div>
      {snapshots.length === 0 ? <p>还没有快照。大改前建议先创建快照。</p> : collapsed ? <p className="muted">快照列表已折叠，避免长历史卡顿。</p> : (
        <div data-windowed-draft-snapshots="true">
          <p className="muted">显示 {windowStart + 1}-{windowEnd} / {orderedSnapshots.length} 个快照。</p>
          {visibleSnapshots.map((snapshot) => (
            <button key={snapshot.snapshot_id} type="button" className="novel-card" onClick={() => onCompare(snapshot.snapshot_id)}>
              <strong>{safeExcerpt(snapshot.title || snapshot.snapshot_id)}</strong>
              <span className="muted">{snapshot.created_at}</span>
            </button>
          ))}
          {orderedSnapshots.length > pageSize ? (
            <div className="pagination-controls" aria-label="草稿快照分页">
              <button type="button" onClick={() => setPageIndex(0)} disabled={clampedPageIndex === 0}>首页</button>
              <button type="button" onClick={() => setPageIndex(Math.max(clampedPageIndex - 1, 0))} disabled={clampedPageIndex === 0}>上一页</button>
              <span>第 {clampedPageIndex + 1} / {pageCount} 页</span>
              <button type="button" onClick={() => setPageIndex(Math.min(clampedPageIndex + 1, pageCount - 1))} disabled={clampedPageIndex >= pageCount - 1}>下一页</button>
              <button type="button" onClick={() => setPageIndex(pageCount - 1)} disabled={clampedPageIndex >= pageCount - 1}>末页</button>
            </div>
          ) : null}
        </div>
      )}
      <p>对比结果只显示 safe summaries，不暴露 hidden World context。</p>
    </NovelSafeSummaryPanel>
  );
}

export function WritingSessionDashboard({ session, currentWordCount }: { session?: WritingSessionState | null; currentWordCount: number }) {
  const active = session && !session.ended_at;
  const delta = session ? currentWordCount - session.word_count_start : 0;
  return (
    <NovelSafeSummaryPanel title="写作会话">
      {session ? (
        <div className="novel-dashboard-grid">
          <NovelMetric title="状态" value={active ? "进行中" : "已结束"} />
          <NovelMetric title="本次字数" value={Math.max(0, delta)} />
          <NovelMetric title="目标" value={session.local_goal_words ?? "未设置"} />
          <NovelMetric title="章节" value={session.active_chapter_id || "无"} />
        </div>
      ) : <p>当前没有写作会话。可以开始写作来本地统计字数。</p>}
      <p>写作会话只是本地 metadata，不上传 telemetry。</p>
    </NovelSafeSummaryPanel>
  );
}

export function WorldToNovelImportPanel({ preview, onPreview }: { preview?: Record<string, unknown> | null; onPreview?: () => void }) {
  const sourceIds = (preview?.source_event_ids as string[] | undefined) ?? [];
  const excluded = Number(preview?.hidden_events_excluded_count ?? preview?.excluded_count ?? 0);
  return (
    <NovelSafeSummaryPanel title="从 World 导入章节草稿">
      <p>预览只使用玩家可见的 safe event summaries。创建 Novel 草稿不会修改 World EventLog 或 GameState，并排除 raw state_deltas。</p>
      {onPreview && <button type="button" onClick={onPreview}>预览 World → Novel 章节草稿</button>}
      <div className="novel-dashboard-grid">
        <NovelMetric title="来源事件" value={sourceIds.length} />
        <NovelMetric title="已过滤" value={excluded} />
        <NovelMetric title="目标" value={String(preview?.target_chapter_id ?? "选择章节")} />
      </div>
      <LinkedRefList title="来源事件范围" refs={sourceIds} />
      <p className="muted">创建或更新 Novel 场景草稿前仍需确认；Tavern/World 原始数据不受影响。</p>
    </NovelSafeSummaryPanel>
  );
}

export function buildNovelQualityIssues(chapters: NovelChapter[], scenes: NovelScene[]): NovelIssue[] {
  const issues: NovelIssue[] = [];
  for (const chapter of chapters) {
    if (!chapter.summary) {
      issues.push({
        severity: "warning",
        code: "missing_chapter_summary",
        category: "continuity",
        ref_type: "chapter",
        ref_id: chapter.chapter_id,
        affected_label: chapter.title,
        message: "Chapter summary is missing.",
        safe_detail: "Chapter has no safe summary for review, export planning, or World Bible cross-checks.",
        suggested_action: "Add a short safe summary before export or World -> Novel import."
      });
    }
    if ((chapter.scene_refs?.length ?? 0) === 0 && scenes.some((scene) => scene.chapter_id === chapter.chapter_id)) {
      issues.push({
        severity: "notice",
        code: "chapter_scene_refs_outdated",
        category: "structure",
        ref_type: "chapter",
        ref_id: chapter.chapter_id,
        affected_label: chapter.title,
        message: "Chapter scene refs may be incomplete.",
        safe_detail: "Scenes exist for this chapter but scene_refs is empty.",
        suggested_action: "Refresh chapter structure links or add scene refs."
      });
    }
  }
  for (const scene of scenes) {
    if (!scene.summary) {
      issues.push({
        severity: "warning",
        code: "missing_scene_summary",
        category: "scene",
        ref_type: "scene",
        ref_id: scene.scene_id,
        affected_label: scene.title,
        message: "Scene summary is missing.",
        safe_detail: "Scene card lacks a safe summary for search, timeline, and export review.",
        suggested_action: "Add a safe one or two sentence scene summary."
      });
    }
  }
  return issues;
}
