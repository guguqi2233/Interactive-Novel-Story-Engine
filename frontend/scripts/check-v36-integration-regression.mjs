import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const read = (...parts) => readFileSync(resolve(root, ...parts), "utf8");
const src = (...parts) => read("src", ...parts);

const app = src("App.tsx");
const api = src("api.ts");
const errorBoundary = src("errorBoundary.tsx");
const safeApiCache = src("safeApiCache.ts");
const packageJson = JSON.parse(read("package.json"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidPattern(source, pattern, label) {
  if (pattern.test(source)) failures.push(`Unexpected ${label}.`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 9000);
}

function requireActiveDebugGate(source, usageToken, label) {
  const usage = source.indexOf(usageToken);
  const gateOpen = source.lastIndexOf("<DebugGate", usage);
  const gateClose = source.lastIndexOf("</DebugGate>", usage);
  if (usage < 0) {
    failures.push(`Missing ${label}: ${usageToken}`);
  } else if (gateOpen < 0 || gateOpen < gateClose) {
    failures.push(`${label} is not rendered inside an active DebugGate region.`);
  }
}

const previousVersionSmokeScripts = [
  "check-v29-ui-safety.mjs",
  "check-v30-local-studio-ux.mjs",
  "check-v31-novel-ui.mjs",
  "check-v32-tavern-ui.mjs",
  "check-v33-world-ui.mjs",
  "check-v34-authoring-ui.mjs",
  "check-v35-qa-debug-provider-ui.mjs"
];

const v36SafetyScripts = [
  "check-v36-eventlog-windowing.mjs",
  "check-v36-timeline-windowing.mjs",
  "check-v36-statedelta-windowing.mjs",
  "check-v36-quality-report-windowing.mjs",
  "check-v36-hidden-leak-windowing.mjs",
  "check-v36-provider-model-list-windowing.mjs",
  "check-v36-provider-status-cache.mjs",
  "check-v36-capability-matrix-performance.mjs",
  "check-v36-search-filter-performance.mjs",
  "check-v36-keyboard-shortcuts.mjs",
  "check-v36-reduced-motion.mjs",
  "check-v36-a11y-semantics.mjs",
  "check-v36-error-boundary.mjs",
  "check-v36-safe-api-cache.mjs",
  "check-v36-performance-a11y.mjs"
];

for (const scriptName of [...previousVersionSmokeScripts, ...v36SafetyScripts]) {
  const scriptPath = resolve(root, "scripts", scriptName);
  if (!existsSync(scriptPath)) {
    failures.push(`Missing check script: ${scriptName}`);
    continue;
  }
  try {
    execFileSync(process.execPath, [scriptPath], {
      cwd: root,
      stdio: "inherit",
      env: {
        ...process.env,
        LLM_PROVIDER: "mock",
        PROVIDER_TEST_MODE: "fake"
      }
    });
  } catch {
    failures.push(`Check script failed: ${scriptName}`);
  }
}

for (const [token, label] of [
  ["function lazyNamed", "route-level lazy import helper"],
  ["lazyNamed(() => import(\"./novelUi\")", "Novel route lazy import"],
  ["lazyNamed(() => import(\"./tavernUi\")", "Tavern route lazy import"],
  ["lazyNamed(() => import(\"./worldUi\")", "World route lazy import"],
  ["<Suspense", "route Suspense fallback"],
  ["<AppErrorBoundary", "route-level safe ErrorBoundary"],
  ["data-windowed-eventlog=\"true\"", "EventLog large-list marker"],
  ["visibleEvents.map((event)", "EventLog visible window rows"],
  ["data-windowed-timeline=\"true\"", "Timeline large-list marker"],
  ["windowedTurns.map((turnGroup)", "Timeline visible window rows"],
  ["data-windowed-statedelta=\"true\"", "StateDelta large-list marker"],
  ["visibleRows.map((row)", "StateDelta visible window rows"],
  ["data-windowed-quality-report=\"true\"", "Quality large-report marker"],
  ["data-windowed-hidden-leak-report=\"true\"", "Hidden Leak large-report marker"],
  ["data-windowed-provider-model-list=\"true\"", "Provider model large-list marker"],
  ["visibleModelRows.map((model)", "Provider model visible window rows"],
  ["SHORTCUT_DANGEROUS_ACTION_BLOCKLIST", "dangerous shortcut blocklist"],
  ["REDUCED_MOTION_PREF_KEY", "reduced motion preference"],
  ["prefers-reduced-motion: reduce", "system reduced motion support"],
  ["aria-label=", "accessibility labels"],
  ["data-v36-safe-api-cache=\"summary-only\"", "safe API cache status panel"]
]) {
  requireToken(app, token, label);
}

requireActiveDebugGate(app, "<StateDeltaViewerPanel", "StateDelta Viewer");

const eventLogPanel = sourceSlice(app, "function EventLogViewerPanel", "function HiddenLeakReportPanel");
if (eventLogPanel.includes("filteredEvents.map(")) {
  failures.push("EventLog normal view maps every filtered event instead of the visible window.");
}
if (/JSON\.stringify\(event/.test(eventLogPanel)) {
  failures.push("EventLog normal view appears to render raw event JSON.");
}

const timelinePanel = sourceSlice(app, "function TimelineReplayPanel", "function filterTimelineTurns");
if (timelinePanel.includes("filteredTurns.map(")) {
  failures.push("Timeline normal view maps every filtered turn instead of the visible window.");
}
const timelineRawDelta = timelinePanel.indexOf("JSON.stringify(redactDebugText(event.state_deltas");
if (timelineRawDelta >= 0 && timelineRawDelta < timelinePanel.indexOf("<DebugGate")) {
  failures.push("Timeline raw StateDelta rendering is not clearly DebugGate-protected.");
}

const stateDeltaPanel = sourceSlice(app, "function StateDeltaViewerPanel", "function buildStateDeltaRows");
if (stateDeltaPanel.includes("filteredRows.map(")) {
  failures.push("StateDelta Viewer maps every filtered row instead of the visible window.");
}
for (const token of ["redactedValue", "Value summary", "StateDelta values are debug-sensitive"]) {
  requireToken(stateDeltaPanel, token, `StateDelta safe debug token ${token}`);
}

const qualityPanel = sourceSlice(app, "function UnifiedQualityGateDashboard", "function buildUnifiedQualityGateRows");
if (qualityPanel.includes("filteredIssues.map(")) {
  failures.push("Quality dashboard maps every filtered issue instead of the visible window.");
}
requireToken(qualityPanel, "safeSummary", "Quality report safe summary rows");

const hiddenLeakPanel = sourceSlice(app, "function HiddenLeakReportPanel", "function buildHiddenLeakIssues");
if (hiddenLeakPanel.includes("filteredIssues.map(")) {
  failures.push("Hidden Leak report maps every filtered issue instead of the visible window.");
}
for (const token of ["redactLeakSummary", "Safe metadata", "Hidden text and secrets are never printed"]) {
  requireToken(app, token, `Hidden Leak safe reporting token ${token}`);
}

const providerPanel = sourceSlice(app, "function ProviderConnectivityDashboard", "function buildProviderConnectivityRow");
if (providerPanel.includes("filteredModelRows.map(")) {
  failures.push("Provider model list maps every filtered model instead of the visible window.");
}
for (const token of ["capabilityBadgesByModelId", "readSafeApiCache", "writeSafeApiCache", "stale", "Manual refresh"]) {
  requireToken(providerPanel + app, token, `Provider safe cache/model-list token ${token}`);
}

for (const token of [
  "const safeApiCacheStore = new Map",
  "containsUnsafeCachePayload",
  "transient",
  "api[_-]?key",
  "raw[_-]?provider",
  "raw[_-]?prompt",
  "raw[_-]?output",
  "hidden[_-]?facts",
  "npc[_-]?secrets",
  "raw[_-]?state",
  "mature[_-]?private"
]) {
  requireToken(safeApiCache, token, `safe API cache boundary ${token}`);
}

for (const forbidden of ["localStorage", "sessionStorage", "indexedDB", "serviceWorker"]) {
  if (safeApiCache.includes(forbidden)) {
    failures.push(`Safe API cache must remain in-memory only; found ${forbidden}.`);
  }
}

for (const token of [
  "formatSafeErrorSummary",
  "stack trace redacted",
  "raw[_\\s-]?env",
  "hidden[_\\s-]?facts?",
  "sensitive local path",
  "Diagnostics remain local-only"
]) {
  requireToken(errorBoundary, token, `ErrorBoundary redaction token ${token}`);
}

const shortcutHandler = sourceSlice(app, "function handleShortcutKeyDown", "const knownFacts");
for (const forbidden of [
  "handleCreateBackup()",
  "handleRestoreDryRun(",
  "handleApplyMigration(",
  "handleDeleteSave(",
  "handleCreateDiagnosticsBundle(",
  "handleModuleQualityGate("
]) {
  if (shortcutHandler.includes(forbidden)) {
    failures.push(`Keyboard shortcut handler directly invokes confirm-gated action: ${forbidden}`);
  }
}

const frontendSource = [app, api, errorBoundary, safeApiCache].join("\n");
forbidPattern(frontendSource, /sk-(live|prod|real)-[A-Za-z0-9_-]+/i, "real-looking API key in frontend source");
forbidPattern(frontendSource, /<input[^>]+name=["']api_key["']/i, "plaintext api_key input");
forbidPattern(frontendSource, /Authorization\s*[:=]\s*["'][^"']+["']/i, "hard-coded Authorization header");

for (const pattern of [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download)\s*<\/button>/i,
  /<a[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download)\s*<\/a>/i,
  /create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i
]) {
  forbidPattern(frontendSource, pattern, "account/cloud/marketplace/remote-download enabling UI");
}

for (const scriptName of [
  "check:v29-ui",
  "check:v30-ux",
  "check:v31-novel-ui",
  "check:v32-tavern-ui",
  "check:v33-world-ui",
  "check:v34-authoring-ui",
  "check:v35-qa-debug-provider-ui",
  "check:v36-performance-a11y"
]) {
  if (!packageJson.scripts?.[scriptName]) {
    failures.push(`package.json is missing ${scriptName}.`);
  }
}

if (failures.length) {
  console.error("v3.6 integration regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 integration regression check passed.");
