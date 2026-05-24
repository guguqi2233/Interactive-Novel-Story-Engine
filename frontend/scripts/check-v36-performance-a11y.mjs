import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const src = (...parts) => readFileSync(resolve(root, "src", ...parts), "utf8");

const app = src("App.tsx");
const styles = src("styles.css");
const novelUi = src("novelUi.tsx");
const tavernUi = src("tavernUi.tsx");
const worldUi = src("worldUi.tsx");
const errorBoundary = src("errorBoundary.tsx");
const safeApiCache = src("safeApiCache.ts");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 9000);
}

function requireAll(source, entries) {
  for (const [token, label] of entries) requireToken(source, token, label);
}

requireAll(app, [
  ["function lazyNamed", "route-level lazy import helper"],
  ["lazyNamed(() => import(\"./novelUi\")", "Novel Studio lazy route imports"],
  ["lazyNamed(() => import(\"./tavernUi\")", "Tavern Studio lazy route imports"],
  ["lazyNamed(() => import(\"./worldUi\")", "World Studio lazy route imports"],
  ["function RouteLoadingBoundary", "route loading/error boundary wrapper"],
  ["<Suspense", "route Suspense fallback"],
  ["<AppErrorBoundary", "route-scoped AppErrorBoundary"],
  ["LoadingState", "safe route loading state"],
  ["SafeErrorState", "safe route error state"]
]);

requireAll(novelUi, [
  ["export function NovelWorkspaceShell", "NovelWorkspaceShell export"],
  ["export function ChapterEditorPro", "ChapterEditorPro export"],
  ["export function SceneCardsBoard", "SceneCardsBoard export"]
]);

requireAll(tavernUi, [
  ["export function TavernWorkspaceShell", "TavernWorkspaceShell export"],
  ["export function SingleCharacterChatPro", "SingleCharacterChatPro export"],
  ["export function TavernMessageListPro", "TavernMessageListPro export"]
]);

requireAll(worldUi, [
  ["export function DebugGate", "DebugGate export"],
  ["export function WorldWorkspaceShell", "WorldWorkspaceShell export"],
  ["export function VisibleStateInspector", "Visible State Inspector export"]
]);

requireAll(app, [
  ["data-windowed-eventlog=\"true\"", "EventLog windowed render marker"],
  ["visibleEvents.map((event)", "EventLog visible window rendering"],
  ["data-windowed-timeline=\"true\"", "Timeline windowed render marker"],
  ["windowedTurns.map((turnGroup)", "Timeline visible turn window rendering"],
  ["data-windowed-statedelta=\"true\"", "StateDelta windowed render marker"],
  ["visibleRows.map((row)", "StateDelta visible row window rendering"],
  ["data-windowed-quality-report=\"true\"", "Quality report windowing marker"],
  ["visibleIssues.map((issue)", "Quality visible issue window rendering"],
  ["data-windowed-hidden-leak-report=\"true\"", "Hidden Leak report windowing marker"],
  ["visibleIssues.map((issue)", "Hidden Leak visible issue window rendering"],
  ["data-windowed-provider-model-list=\"true\"", "Provider model list windowing marker"],
  ["visibleModelRows.map((model)", "Provider visible model window rendering"],
  ["data-windowed-module-browser=\"true\"", "Module Browser windowing marker"],
  ["visibleModules.map((module)", "Module Browser visible package window rendering"],
  ["data-windowed-compatibility-matrix=\"true\"", "Compatibility matrix windowing marker"]
]);

const eventLogPanel = sourceSlice(app, "function EventLogViewerPanel", "function HiddenLeakReportPanel");
if (eventLogPanel.includes("filteredEvents.map(")) {
  failures.push("EventLog Viewer maps all filtered events instead of the visible window.");
}
if (eventLogPanel.includes("JSON.stringify(event")) {
  failures.push("EventLog Viewer normal panel renders raw event JSON.");
}

const timelinePanel = sourceSlice(app, "function TimelineReplayPanel", "function filterTimelineTurns");
if (timelinePanel.includes("filteredTurns.map(")) {
  failures.push("Timeline Replay maps all filtered turns instead of windowed turns.");
}
if (timelinePanel.includes("raw_state_delta") || timelinePanel.includes("raw state_deltas")) {
  failures.push("Timeline Replay normal panel appears to reference raw state deltas.");
}
if (timelinePanel.includes('{error && <p className="error">{error}</p>}') || timelinePanel.includes('{dryRunError && <p className="error">{dryRunError}</p>}')) {
  failures.push("Timeline Replay displays raw error text without redaction.");
}

const stateDeltaUsageIndex = app.indexOf("<StateDeltaViewerPanel");
const debugGateBeforeStateDelta = app.lastIndexOf("<DebugGate", stateDeltaUsageIndex);
const debugGateCloseBeforeStateDelta = app.lastIndexOf("</DebugGate>", stateDeltaUsageIndex);
if (stateDeltaUsageIndex < 0) {
  failures.push("StateDeltaViewerPanel usage is missing.");
} else if (debugGateBeforeStateDelta < 0 || debugGateBeforeStateDelta < debugGateCloseBeforeStateDelta) {
  failures.push("StateDeltaViewerPanel is not rendered inside an active DebugGate region.");
}

const eventLogCard = sourceSlice(app, "function EventLogSafeCard", "function sortedUnique");
if (!eventLogCard.includes("DebugGate")) {
  failures.push("EventLog raw detail area is not clearly DebugGate wrapped.");
}

requireAll(app, [
  ["function KeyboardShortcutsProvider", "keyboard shortcuts provider"],
  ["function ShortcutHelpDialog", "shortcut help UI"],
  ["SHORTCUT_DANGEROUS_ACTION_BLOCKLIST", "dangerous shortcut blocklist"],
  ["data-v36-keyboard-shortcuts=\"safe-foundation\"", "keyboard shortcut safety marker"],
  ["REDUCED_MOTION_PREF_KEY", "reduced motion setting"],
  ["prefers-reduced-motion: reduce", "system reduced motion preference"],
  ["aria-label=\"Open keyboard shortcuts help\"", "shortcut help accessible label"],
  ["function safeAriaText", "safe aria text sanitizer"],
  ["role=\"group\" aria-label=\"Filter controls\"", "filter toolbar semantics"],
  ["aria-live=\"polite\"", "polite live status"],
  ["aria-live=\"assertive\"", "assertive error state"],
  ["data-v36-safe-api-cache=\"summary-only\"", "safe API cache marker"]
]);

requireAll(styles, [
  [".reduced-motion-root", "reduced motion root styles"],
  ["@media (prefers-reduced-motion: reduce)", "reduced motion media query"],
  [".eventlog-window-toolbar", "EventLog/Timeline/StateDelta window toolbar styles"],
  [".quality-issue-browser", "Quality large report styles"],
  [".hidden-leak-issue-browser", "Hidden Leak large report styles"],
  [".provider-model-list", "Provider model list styles"],
  [".safe-api-cache-panel", "safe API cache status styles"]
]);

requireAll(errorBoundary, [
  ["export class AppErrorBoundary", "AppErrorBoundary export"],
  ["redactBoundaryError", "ErrorBoundary safe redaction"],
  ["stack trace redacted", "ErrorBoundary stack redaction"],
  ["Diagnostics remain local-only", "safe diagnostics hint"]
]);

requireAll(safeApiCache, [
  ["const safeApiCacheStore = new Map", "in-memory safe API cache"],
  ["containsUnsafeCachePayload", "unsafe cache payload rejection"],
  ["transient", "transient key rejection coverage"],
  ["raw[_-]?prompt", "raw prompt rejection coverage"],
  ["raw[_-]?output", "raw output rejection coverage"],
  ["hidden[_-]?facts", "hidden fact rejection coverage"],
  ["raw[_-]?state", "raw state delta rejection coverage"],
  ["mature[_-]?private", "mature/private rejection coverage"]
]);

for (const forbiddenCacheStorage of ["localStorage", "sessionStorage", "indexedDB", "serviceWorker"]) {
  if (safeApiCache.includes(forbiddenCacheStorage)) {
    failures.push(`Safe API cache must remain in-memory only; found ${forbiddenCacheStorage}.`);
  }
}

const sourceBundle = [app, novelUi, tavernUi, worldUi, errorBoundary, safeApiCache].join("\n");
if (/sk-[A-Za-z0-9_-]{12,}/.test(sourceBundle)) {
  failures.push("Secret-looking sk-* token detected in frontend source.");
}
if (/<input[^>]+name=["']api_key["']/i.test(sourceBundle)) {
  failures.push("Plaintext api_key input detected in frontend UI.");
}
if (/Authorization\s*[:=]\s*["'][^"']+["']/i.test(sourceBundle)) {
  failures.push("Authorization header literal detected in frontend source.");
}
const timelineDebugOpenIndex = timelinePanel.indexOf("<DebugGate");
const timelineRawDeltaIndex = timelinePanel.indexOf("JSON.stringify(redactDebugText(event.state_deltas");
if (timelineRawDeltaIndex >= 0 && (timelineDebugOpenIndex < 0 || timelineRawDeltaIndex < timelineDebugOpenIndex)) {
  failures.push("Timeline Replay raw StateDelta JSON is not clearly behind DebugGate.");
}

const forbiddenOnlineEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download|Online Play)\s*<\/button>/i,
  /<a[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download|Online Play)\s*<\/a>/i,
  /create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i
];
for (const pattern of forbiddenOnlineEntrypoints) {
  if (pattern.test(sourceBundle)) {
    failures.push("Account/cloud/online marketplace/remote download appears as an enabling UI entrypoint.");
  }
}

const requiredScripts = [
  "check:v36-performance-a11y",
  "check:v36-eventlog-windowing",
  "check:v36-timeline-windowing",
  "check:v36-statedelta-windowing",
  "check:v36-quality-report-windowing",
  "check:v36-hidden-leak-windowing",
  "check:v36-provider-model-list-windowing",
  "check:v36-error-boundary",
  "check:v36-keyboard-shortcuts",
  "check:v36-reduced-motion",
  "check:v36-a11y-semantics",
  "check:v36-safe-api-cache"
];
for (const scriptName of requiredScripts) {
  if (!pkg.scripts?.[scriptName]) {
    failures.push(`package.json is missing ${scriptName}.`);
  }
}

if (!existsSync(resolve(root, "scripts", "check-v36-performance-a11y.mjs"))) {
  failures.push("check-v36-performance-a11y.mjs is missing.");
}

if (failures.length) {
  console.error("v3.6 performance/a11y regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 performance/a11y regression check passed.");
