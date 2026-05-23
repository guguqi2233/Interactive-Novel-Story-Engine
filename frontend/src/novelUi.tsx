import { ReactNode } from "react";
import { NovelChapter, NovelManuscript, NovelScene } from "./api";

export type NovelIssue = {
  severity: string;
  code: string;
  message: string;
  ref_type?: string;
  ref_id?: string;
  safe_detail?: string;
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
  const value = (text ?? "").replace(/(api[_\s-]?key|authorization|hidden[_\s-]?fact|state[_\s-]?delta|raw[_\s-]?prompt)\s*[:=]\s*[^\n,;]+/gi, "$1=[redacted]");
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

export function OutlineTreePro() {
  return <NovelSafeSummaryPanel title="Outline Tree Pro"><p>Act, volume, chapter, scene, beat, and note nodes use local outline APIs.</p></NovelSafeSummaryPanel>;
}

export function ChapterEditorPro({ children }: { children: ReactNode }) {
  return <div className="chapter-editor-pro">{children}</div>;
}

export function SceneCardsBoard({ scenes }: { scenes: NovelScene[] }) {
  return <div className="scene-cards-board">{scenes.map((scene) => <SceneCard key={scene.scene_id} scene={scene} />)}</div>;
}

export function CharacterArcPanel() {
  return <NovelSafeSummaryPanel title="Character Arc Panel"><p>Character arcs show public premises, states, turning point counts, and linked safe refs.</p></NovelSafeSummaryPanel>;
}

export function PlotForeshadowingBoard() {
  return <NovelSafeSummaryPanel title="Plot / Foreshadowing Board"><p>Hidden truth refs are represented as redacted labels in normal view.</p></NovelSafeSummaryPanel>;
}

export function TimelineLinkPanel() {
  return <NovelSafeSummaryPanel title="Timeline Link Panel"><p>Linked timeline and world events are shown as safe summaries only.</p></NovelSafeSummaryPanel>;
}

export function WorldBibleSidebar() {
  return <NovelSafeSummaryPanel title="World Bible Sidebar"><p>Flavor lore and novel-safe structured facts can be reviewed without NPC secrets.</p></NovelSafeSummaryPanel>;
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
      {issues.length === 0 ? <p>No report yet. Run local Novel quality checks before export.</p> : issues.map((issue) => (
        <p key={`${issue.code}-${issue.ref_id ?? ""}`}>
          <strong>{safeExcerpt(issue.severity)}</strong> {safeExcerpt(issue.safe_detail || issue.message)}
        </p>
      ))}
    </NovelSafeSummaryPanel>
  );
}

export function NovelSearchFilterBar({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="novel-search-bar">
      Search Novel Studio
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder="Search chapters, scenes, plot threads" />
    </label>
  );
}
