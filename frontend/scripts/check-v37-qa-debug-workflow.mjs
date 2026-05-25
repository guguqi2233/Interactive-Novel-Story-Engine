import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 30000);
}

requireToken(app, "function QADebugReplayCompleteWorkflowChecklist", "QA / Debug / Replay Complete Workflow Check component");
requireToken(app, "data-v37-qa-debug-workflow-check=\"safe-summary\"", "v3.7 QA / Debug workflow safe summary marker");
requireToken(app, "buildQADebugReplayWorkflowChecklistItems", "QA / Debug workflow checklist builder");
requireToken(app, "QA / Debug / Replay readiness", "Product dashboard QA readiness item");
requireToken(app, "Debug UI cannot mutate GameState", "Debug cannot mutate GameState boundary copy");
requireToken(app, "Replay does not write EventLog or state", "Replay read-only boundary copy");
requireToken(app, "diagnostics are not uploaded", "diagnostics local-only copy");
requireToken(app, "raw state_deltas remain debug-gated", "raw StateDelta debug gate copy");
requireToken(app, "normal reports never print hidden text or secrets", "hidden text normal-report exclusion copy");
requireToken(app, "Debug disabled state is clear", "debug disabled state copy");

for (const label of [
  "Unified Quality Dashboard available",
  "Timeline Replay available",
  "EventLog Viewer available",
  "StateDelta Viewer debug-gated",
  "Visible vs Debug Compare available",
  "Hidden Leak Report available",
  "Playtest Dashboard available",
  "Module Stress available",
  "Save Migration Visualizer available",
  "Diagnostics Review available",
  "Safe Debug Export available",
  "Debug UI cannot mutate GameState",
  "raw state_deltas debug-gated",
  "no hidden text in normal reports"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const token of [
  "UnifiedQualityGateDashboard",
  "Quality Gate Unified Dashboard Pro",
  "TimelineReplayPanel",
  "Timeline Replay UI Pro",
  "EventLogViewerPanel",
  "EventLog Viewer Pro",
  "StateDeltaViewerPanel",
  "StateDelta Viewer Pro",
  "VisibleDebugStateCompare",
  "Visible vs Debug State Compare",
  "HiddenLeakReportPanel",
  "Hidden Leak Report UI Pro",
  "PlaytestingDashboard",
  "Playtest Dashboard Pro",
  "ModulePlaytestStressProPanel",
  "Module Playtest / Stress UI Pro",
  "MigrationPanel",
  "Save Migration Visualizer",
  "DiagnosticsBundlePanel",
  "Diagnostics Bundle Review UI",
  "SafeDebugExportWizard",
  "Safe Debug Export Wizard",
  "DebugGate"
]) {
  requireToken(app, token, `${token} QA / Debug integration`);
}

requireToken(app, "debugEnabled ? \"ready\" : \"disabled\"", "debug disabled pass status path");
requireToken(app, "diagnosticsRedacted ? \"ready\"", "diagnostics redacted ready status path");
requireToken(app, "!diagnosticsBundlePreview.manifest.contains_secrets", "diagnostics secret exclusion check");
requireToken(app, "!diagnosticsBundlePreview.manifest.contains_hidden_debug_mature_private", "diagnostics hidden/debug/mature exclusion check");
requireToken(app, "Normal QA views show safe event summaries and StateDelta counts only", "raw deltas excluded from normal view copy");
requireToken(app, "Normal QA reports redact hidden text, NPC secrets, debug memory, raw prompts, raw outputs", "normal report hidden redaction copy");
requireToken(app, "Run local playtests with fake/local providers only", "no real provider playtest copy");

const checklist = sourceSlice(app, "function QADebugReplayCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "refreshDiagnosticsBundlePreview(",
  "handlePreviewDiagnosticsBundle(",
  "handleCreateDiagnosticsBundle(",
  "createDiagnosticsBundle(",
  "previewDiagnosticsBundle(",
  "runWorldHealth(",
  "handleRunPlaytest(",
  "handleRunPlaytestBatch(",
  "refreshTimeline(",
  "refreshTimelineReplay(",
  "refreshDebugGraphs(",
  "handleDryRunMigration(",
  "handleApplyMigration(",
  "applyMigration(",
  "applyStateDelta",
  "submitPlayerInput(",
  "setVisibleState(",
  "setGameState(",
  "fetch(",
  "testProjectProviderConnection(",
  "fetchProjectProviderModels(",
  "syncProjectProviderModels("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`QA / Debug workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("QA / Debug workflow checklist includes API-key input or transient key terminology outside safe exclusion copy.");
}

if (/JSON\.stringify\([^)]*state_delta/i.test(checklist) || /<pre>/i.test(checklist)) {
  failures.push("QA / Debug workflow checklist appears to render raw debug payloads.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(app)) {
  failures.push("Secret-looking sk-* token detected in QA / Debug workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|OnlineDiagnosticsUpload)/i.test(app)) {
  failures.push("Online/account/cloud/marketplace/diagnostics-upload enabling entrypoint detected in QA / Debug workflow source.");
}

if (!pkg.scripts?.["check:v37-qa-debug-workflow"]) {
  failures.push("package.json is missing check:v37-qa-debug-workflow.");
}

if (failures.length) {
  console.error("v3.7 QA / Debug / Replay workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 QA / Debug / Replay workflow check passed.");
