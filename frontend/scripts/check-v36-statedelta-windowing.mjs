import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function StateDeltaViewerPanel");
const panelEnd = appSource.indexOf("function flattenStateDeltaRows", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("StateDeltaViewerPanel source slice not found.");

const requiredWindowingTokens = [
  "pageSize",
  "pageIndex",
  "visibleRows",
  "filteredRows.slice(windowStart, windowEnd)",
  "data-windowed-statedelta",
  "data-rendered-count",
  "Path prefix",
  "Path search",
  "Event id",
  "Event type",
  "StateDelta Viewer Pro",
  "ENABLE_DEBUG_API required"
];

for (const token of requiredWindowingTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing StateDelta windowing/filter token: ${token}`);
}

if (panelSource.includes("filteredRows.map(")) {
  failures.push("StateDeltaViewerPanel still maps all filtered rows instead of only the visible window.");
}

if (!panelSource.includes("visibleRows.map(")) {
  failures.push("StateDeltaViewerPanel does not render the visible StateDelta row window.");
}

if (!panelSource.includes("row.valueSummary")) {
  failures.push("StateDeltaViewerPanel does not default to the redacted value summary.");
}

if (!panelSource.includes("Debug redacted value detail") || !panelSource.includes("row.redactedValue")) {
  failures.push("StateDelta expanded value detail is missing or not redacted.");
}

const flattenStart = appSource.indexOf("function flattenStateDeltaRows");
const flattenEnd = appSource.indexOf("function summarizeStateDeltaValue", flattenStart);
const flattenSource = flattenStart >= 0 && flattenEnd > flattenStart ? appSource.slice(flattenStart, flattenEnd) : "";
if (!flattenSource.includes("redactedValue: redactDebugText(delta.value)")) {
  failures.push("StateDelta rows do not store redacted values for expanded debug detail.");
}

const viewerUsage = appSource.indexOf("<StateDeltaViewerPanel events={timeline} />");
const gateBeforeViewer = appSource.lastIndexOf("<DebugGate", viewerUsage);
const gateCloseBeforeViewer = appSource.lastIndexOf("</DebugGate>", viewerUsage);
if (viewerUsage < 0 || gateBeforeViewer < 0 || gateCloseBeforeViewer > gateBeforeViewer) {
  failures.push("StateDeltaViewerPanel is not clearly rendered inside DebugGate.");
}

if (!styleSource.includes(".statedelta-window-toolbar")) {
  failures.push("Missing StateDelta window toolbar styles.");
}
if (!styleSource.includes(".statedelta-value-detail")) {
  failures.push("Missing StateDelta redacted value detail styles.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in StateDelta UI source.");
}

if (failures.length) {
  console.error("v3.6 StateDelta windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 StateDelta windowing check passed.");
