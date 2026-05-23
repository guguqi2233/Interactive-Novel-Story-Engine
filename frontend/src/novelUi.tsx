import { ReactNode, useMemo, useState } from "react";
import { NovelChapter, NovelDraftSnapshot, NovelManuscript, NovelScene, WritingSessionState } from "./api";

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

function wordCount(text?: string | null): number {
  return (text ?? "").split(/\s+/).filter(Boolean).length;
}

function safeExcerpt(text?: string | null, max = 160): string {
  const value = (text ?? "").replace(/(api[_\s-]?key|authorization|hidden[_\s-]?fact|npc[_\s-]?secret|private[_\s-]?note|state[_\s-]?delta|raw[_\s-]?prompt)\s*[:=]\s*[^\n,;]+/gi, "$1=[redacted]");
  return value.length > max ? `${value.slice(0, max)}...` : value;
}

export function NovelStatusBadge({ status }: { status?: string | null }) {
  const value = status || "draft";
  return <span className={`novel-status-badge novel-status-${value}`}>{value}</span>;
}

export function WordCountBadge({ text, count }: { text?: string | null; count?: number }) {
  return <span className="word-count-badge">{count ?? wordCount(text)} words</span>;
}

export function LinkedRefList({ title, refs }: { title: string; refs?: string[] }) {
  const safeRefs = (refs ?? []).filter(Boolean);
  return (
    <div className="linked-ref-list">
      <strong>{title}</strong>
      {safeRefs.length === 0 ? <span className="muted">none</span> : safeRefs.map((ref) => <span key={ref}>{ref}</span>)}
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
        <p className="muted">{safeExcerpt(manuscript.description) || "Local manuscript draft."}</p>
      </div>
      <div className="novel-card-meta">
        <span>{manuscript.chapter_refs?.length ?? 0} linked chapters</span>
        <span>{manuscript.genre_tags?.join(", ") || "untagged"}</span>
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
      <p className="muted">{safeExcerpt(chapter.summary) || "No chapter summary."}</p>
      <div className="novel-card-meta">
        <WordCountBadge text={chapter.draft_text} />
        <span>{chapter.scene_refs?.length ?? 0} scenes</span>
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
      <p className="muted">{safeExcerpt(scene.summary) || "No scene summary."}</p>
      <div className="novel-card-meta">
        <span>chapter {scene.chapter_id}</span>
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
      <p className="muted">Normal Novel UI excludes API keys, hidden facts, private notes, raw prompts, and raw state_deltas.</p>
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
      {saving ? "saving..." : dirty ? "unsaved changes" : message || "saved locally"}
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
  const words = chapters.reduce((total, chapter) => total + wordCount(chapter.draft_text), 0) + scenes.reduce((total, scene) => total + wordCount(scene.draft_text), 0);
  return (
    <div className="novel-dashboard-grid">
      <NovelMetric title="Manuscripts" value={manuscripts.length} />
      <NovelMetric title="Chapters" value={chapters.length} />
      <NovelMetric title="Scenes" value={scenes.length} />
      <NovelMetric title="Total words" value={words} />
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
  const orderedChapters = [...chapters].sort((left, right) => left.order_index - right.order_index);

  if (orderedChapters.length === 0) {
    return (
      <NovelSafeSummaryPanel title="Outline Tree Pro">
        <p>No outline nodes yet. Add a chapter to start building a local manuscript structure.</p>
      </NovelSafeSummaryPanel>
    );
  }

  return (
    <NovelSafeSummaryPanel title="Outline Tree Pro">
      <div className="outline-tree-pro">
        {orderedChapters.map((chapter, index) => {
          const childScenes = scenes.filter((scene) => scene.chapter_id === chapter.chapter_id);
          const isCollapsed = collapsed.has(chapter.chapter_id);
          const missing = [
            !chapter.summary ? "summary" : "",
            childScenes.length === 0 ? "scene" : ""
          ].filter(Boolean);
          return (
            <div key={chapter.chapter_id} className={`outline-tree-node ${chapter.chapter_id === selectedChapterId ? "selected" : ""}`}>
              <button type="button" className="outline-tree-row" onClick={() => onSelectChapter?.(chapter.chapter_id)}>
                <span className="outline-node-type">chapter</span>
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
                  {isCollapsed ? "Expand" : "Collapse"}
                </button>
                <button type="button" disabled title="Reorder writes are available through outline APIs only after validation.">Move</button>
                <span>{childScenes.length} scene(s)</span>
                {missing.length > 0 && <span className="novel-warning-chip">missing {missing.join(", ")}</span>}
              </div>
              {!isCollapsed && (
                <div className="outline-tree-children">
                  {childScenes.length === 0 ? <p className="muted">No scene cards linked yet.</p> : childScenes.map((scene) => (
                    <OutlineNodeView
                      key={scene.scene_id}
                      depth={1}
                      node={{
                        node_id: scene.scene_id,
                        node_type: "scene",
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

export function SceneCardsBoard({ scenes }: { scenes: NovelScene[] }) {
  const [filter, setFilter] = useState("");
  const [status, setStatus] = useState("all");
  const filtered = scenes.filter((scene) => {
    const haystack = [scene.title, scene.summary, scene.status, scene.pov_character_id, scene.location_ref, ...(scene.linked_character_ids ?? [])].join(" ").toLowerCase();
    return (!filter || haystack.includes(filter.toLowerCase())) && (status === "all" || (scene.status || "draft") === status);
  });
  const statuses = ["all", ...uniqueRefs(scenes.map((scene) => scene.status || "draft"))];
  return (
    <div className="stack">
      <NovelToolbar
        title="Scene Cards Board"
        meta={<span className="muted">POV, location, characters, status, tags, word count, and plot refs stay local to Novel drafts.</span>}
        actions={(
          <>
            <input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="Filter scenes, tags, POV, location" />
            <select value={status} onChange={(event) => setStatus(event.target.value)}>
              {statuses.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </>
        )}
      />
      {filtered.length === 0 ? <p className="muted">No scenes match this filter.</p> : (
        <div className="scene-cards-board">
          {filtered.map((scene) => (
            <div key={scene.scene_id} className="scene-card-pro">
              <SceneCard scene={scene} />
              <div className="novel-card-meta">
                <span>POV {scene.pov_character_id || "unset"}</span>
                <span>location {scene.location_ref || "unset"}</span>
                <span>plot {scene.linked_world_event_ids?.[0] || "unlinked"}</span>
              </div>
              <div className="novel-chip-row">
                {sceneTags(scene).map((tag) => <span key={tag} className="novel-chip">{safeExcerpt(tag, 40)}</span>)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function CharacterArcPanel({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const characterIds = uniqueRefs([
    ...chapters.flatMap((chapter) => chapter.linked_character_ids ?? []),
    ...scenes.flatMap((scene) => scene.linked_character_ids ?? []),
    ...scenes.map((scene) => scene.pov_character_id)
  ]);
  return (
    <NovelSafeSummaryPanel title="Character Arc Panel">
      {characterIds.length === 0 ? <p>No linked characters yet. Add character refs to chapters or scenes to track arcs.</p> : characterIds.map((characterId) => {
        const linkedScenes = scenes.filter((scene) => scene.pov_character_id === characterId || scene.linked_character_ids?.includes(characterId));
        const linkedChapters = chapters.filter((chapter) => chapter.linked_character_ids?.includes(characterId) || linkedScenes.some((scene) => scene.chapter_id === chapter.chapter_id));
        const stage = linkedScenes.length >= 3 ? "turning point ready" : linkedScenes.length > 0 ? "setup" : "unlinked";
        return (
          <div key={characterId} className="novel-card compact">
            <div className="novel-card-title-row">
              <strong>{safeExcerpt(characterId)}</strong>
              <NovelStatusBadge status={stage} />
            </div>
            <p className="muted">Motivation/conflict notes remain authoring material. Turning points are inferred from linked safe scenes.</p>
            <LinkedRefList title="linked chapters" refs={linkedChapters.map((chapter) => chapter.chapter_id)} />
            <LinkedRefList title="turning points" refs={linkedScenes.slice(0, 4).map((scene) => scene.scene_id)} />
          </div>
        );
      })}
    </NovelSafeSummaryPanel>
  );
}

export function PlotForeshadowingBoard({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const linkedWorldEvents = uniqueRefs(scenes.flatMap((scene) => scene.linked_world_event_ids ?? []));
  const unresolvedScenes = scenes.filter((scene) => !scene.summary || (scene.status || "draft") !== "complete");
  return (
    <NovelSafeSummaryPanel title="Plot / Foreshadowing Board">
      <div className="novel-dashboard-grid">
        <NovelMetric title="Plot refs" value={linkedWorldEvents.length} />
        <NovelMetric title="Open scenes" value={unresolvedScenes.length} />
        <NovelMetric title="Chapters" value={chapters.length} />
      </div>
      {linkedWorldEvents.length === 0 ? <p className="muted">No plot thread refs yet.</p> : <LinkedRefList title="plot threads / world refs" refs={linkedWorldEvents} />}
      {unresolvedScenes.slice(0, 5).map((scene) => (
        <p key={scene.scene_id}><strong>{safeExcerpt(scene.title)}</strong>: setup/payoff status needs review. Hidden truth refs are redacted in normal view.</p>
      ))}
    </NovelSafeSummaryPanel>
  );
}

export function TimelineLinkPanel({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const timelineRefs = uniqueRefs([
    ...chapters.flatMap((chapter) => chapter.linked_timeline_event_ids ?? []),
    ...scenes.flatMap((scene) => scene.timeline_event_refs ?? []),
    ...scenes.flatMap((scene) => scene.linked_world_event_ids ?? [])
  ]);
  return (
    <NovelSafeSummaryPanel title="Timeline Link Panel">
      {timelineRefs.length === 0 ? <p>No safe timeline refs linked yet.</p> : <LinkedRefList title="safe timeline / world event refs" refs={timelineRefs} />}
      <p>Timeline refs are reference-only; Novel UI cannot write World EventLog or GameState.</p>
    </NovelSafeSummaryPanel>
  );
}

export function WorldBibleSidebar({ chapters = [], scenes = [] }: { chapters?: NovelChapter[]; scenes?: NovelScene[] }) {
  const factRefs = uniqueRefs([
    ...chapters.flatMap((chapter) => chapter.linked_fact_ids ?? []),
    ...scenes.flatMap((scene) => scene.linked_fact_ids ?? [])
  ]);
  return (
    <NovelSafeSummaryPanel title="World Bible Sidebar">
      {factRefs.length === 0 ? <p>No novel-safe World Bible refs linked yet.</p> : <LinkedRefList title="novel-safe fact refs" refs={factRefs} />}
      <p>World facts are safe references for drafting only; hidden facts and NPC secrets stay out of normal Novel UI.</p>
    </NovelSafeSummaryPanel>
  );
}

export function NovelPromptProviderPanel({ promptProfileId, providerSummary }: { promptProfileId?: string | null; providerSummary?: string }) {
  return (
    <NovelSafeSummaryPanel title="Novel Prompt / Provider">
      <p>Prompt profile: {promptProfileId || "project default"}</p>
      <p>Provider: {providerSummary || "safe summary only; API key not shown"}</p>
      <p>Use cases: novel_draft / novel_rewrite / chapter_summary.</p>
    </NovelSafeSummaryPanel>
  );
}

export function NovelExportWizard({ onExportMarkdown, onExportTxt }: { onExportMarkdown: () => void; onExportTxt: () => void }) {
  return (
    <NovelSafeSummaryPanel title="Novel Export Wizard">
      <p>Markdown / TXT export preview excludes authoring notes, hidden refs, mature/private content, debug data, and API keys by default.</p>
      <div className="button-row">
        <button type="button" onClick={onExportMarkdown}>Export Markdown</button>
        <button type="button" onClick={onExportTxt}>Export TXT</button>
      </div>
    </NovelSafeSummaryPanel>
  );
}

export function NovelQualityDashboard({ issues }: { issues: NovelIssue[] }) {
  return (
    <NovelSafeSummaryPanel title="Novel Quality Dashboard">
      {issues.length === 0 ? <p>No report yet. Run local Novel quality checks before export.</p> : (
        <div className="novel-quality-list">
          {issues.map((issue) => (
            <div key={`${issue.code}-${issue.ref_id ?? issue.message}`} className={`novel-quality-row severity-${issue.severity}`}>
              <div className="novel-card-title-row">
                <strong>{safeExcerpt(issue.severity)}</strong>
                <span>{safeExcerpt(issue.category || issue.code)}</span>
              </div>
              <p>{safeExcerpt(issue.safe_detail || issue.message)}</p>
              <p className="muted">Affected: {safeExcerpt(issue.affected_label || [issue.ref_type, issue.ref_id].filter(Boolean).join(":") || "manuscript")}</p>
              <p className="muted">Suggested action: {safeExcerpt(issue.suggested_action || "Review the affected draft and rerun local quality checks.")}</p>
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
  return (
    <div className="novel-search-bar">
      <label>
        Search Novel Studio
        <input value={value} onChange={(event) => onChange(event.target.value)} placeholder="Search chapters, scenes, plot threads" />
      </label>
      <label>
        Status
        <select value={status || ""} onChange={(event) => onStatusChange?.(event.target.value)}>
          <option value="">any</option>
          <option value="draft">draft</option>
          <option value="revision">revision</option>
          <option value="complete">complete</option>
        </select>
      </label>
      <label>
        Tag
        <input value={tag || ""} onChange={(event) => onTagChange?.(event.target.value)} placeholder="character, plot, location" />
      </label>
    </div>
  );
}

export function DraftVersionPanel({ snapshots, onCompare }: { snapshots: NovelDraftSnapshot[]; onCompare: (snapshotId: string) => void }) {
  return (
    <NovelSafeSummaryPanel title="Draft Version Compare">
      {snapshots.length === 0 ? <p>No snapshots yet. Create one before a major rewrite.</p> : snapshots.map((snapshot) => (
        <button key={snapshot.snapshot_id} type="button" className="novel-card" onClick={() => onCompare(snapshot.snapshot_id)}>
          <strong>{safeExcerpt(snapshot.title || snapshot.snapshot_id)}</strong>
          <span className="muted">{snapshot.created_at}</span>
        </button>
      ))}
      <p>Compare results are safe summaries and never expose hidden World context.</p>
    </NovelSafeSummaryPanel>
  );
}

export function WritingSessionDashboard({ session, currentWordCount }: { session?: WritingSessionState | null; currentWordCount: number }) {
  const active = session && !session.ended_at;
  const delta = session ? currentWordCount - session.word_count_start : 0;
  return (
    <NovelSafeSummaryPanel title="Writing Session Dashboard">
      {session ? (
        <div className="novel-dashboard-grid">
          <NovelMetric title="Status" value={active ? "active" : "ended"} />
          <NovelMetric title="Words this session" value={Math.max(0, delta)} />
          <NovelMetric title="Goal" value={session.local_goal_words ?? "unset"} />
          <NovelMetric title="Chapter" value={session.active_chapter_id || "none"} />
        </div>
      ) : <p>No active writing session. Start one for local word-count tracking.</p>}
      <p>Writing sessions are local metadata; no telemetry is uploaded.</p>
    </NovelSafeSummaryPanel>
  );
}

export function WorldToNovelImportPanel({ preview }: { preview?: Record<string, unknown> | null }) {
  const sourceIds = (preview?.source_event_ids as string[] | undefined) ?? [];
  const excluded = Number(preview?.hidden_events_excluded_count ?? preview?.excluded_count ?? 0);
  return (
    <NovelSafeSummaryPanel title="World -> Novel Import UX Pro">
      <p>Preview uses safe event summaries only. Apply confirmation does not modify World EventLog or GameState, and raw state_deltas are excluded.</p>
      <div className="novel-dashboard-grid">
        <NovelMetric title="Source events" value={sourceIds.length} />
        <NovelMetric title="Filtered" value={excluded} />
        <NovelMetric title="Target" value={String(preview?.target_chapter_id ?? "choose chapter")} />
      </div>
      <LinkedRefList title="source event range" refs={sourceIds} />
      <p className="muted">Confirm before creating or updating any Novel scene draft. Tavern/World originals are untouched.</p>
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
