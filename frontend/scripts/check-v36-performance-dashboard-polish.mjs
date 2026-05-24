import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function PerformanceDashboard");
const panelEnd = appSource.indexOf("function PlaytestingDashboard", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("PerformanceDashboard source slice not found.");

for (const [token, label] of [
  ["data-v36-performance-dashboard-polish", "v3.6.19 marker"],
  ["Local Performance Dashboard Polish", "dashboard title"],
  ["frontend large list warnings", "frontend large list warning metric"],
  ["provider latency", "provider latency metric"],
  ["quality gate duration", "quality gate duration metric"],
  ["playtest duration", "playtest duration metric"],
  ["save/load duration", "save/load duration metric"],
  ["diagnostics duration", "diagnostics duration metric"],
  ["event count", "event count metric"],
  ["model count", "model count metric"],
  ["PERFORMANCE_METRIC_CATEGORY_FILTERS", "category filter options"],
  ["categoryFilter", "category filter state"],
  ["optimizationHint", "optimization hint field"],
  ["Optimization Hints", "optimization hints section"],
  ["No telemetry upload", "no telemetry wording"],
  ["No prompt/output full text", "prompt/output exclusion wording"],
  ["hidden facts", "hidden facts exclusion wording"],
  ["API key", "API key exclusion wording"],
  ["buildPerformanceProRows(entries, samples, { eventCount, modelCount, playtestBatchReport })", "safe aggregate builder wiring"],
  ["eventCountFromSamples", "event count safe aggregate helper"],
  ["modelCountFromSamples", "model count safe aggregate helper"],
  ["playtestBatchReport.performance_summary", "playtest duration aggregate"],
  ["Provider Gateway latency only", "provider safe summary wording"]
]) {
  if (!appSource.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

if (/SafeJSON|<pre>|Authorization\s*[:=]|transient_api_key\s*[:=]/i.test(panelSource)) {
  failures.push("Performance dashboard appears to render raw JSON, auth headers, or transient key data.");
}

if (/prompt\s*[:=]|output\s*[:=]|hidden[_ -]?fact\s*[:=]|api[_ -]?key\s*[:=]/i.test(panelSource)) {
  failures.push("Performance dashboard contains risky prompt/output/hidden/API-key field rendering patterns.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in frontend source.");
}

if (!/"check:v36-performance-dashboard-polish"/.test(pkg)) {
  failures.push("package.json is missing check:v36-performance-dashboard-polish.");
}

if (failures.length) {
  console.error("v3.6 Local Performance Dashboard Polish check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Local Performance Dashboard Polish check passed.");
