import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function EventLogViewerPanel");
const panelEnd = appSource.indexOf("const HIDDEN_LEAK_CATEGORIES", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("EventLogViewerPanel source slice not found.");

const requiredWindowingTokens = [
  "pageSize",
  "pageIndex",
  "visibleEvents",
  "filteredEvents.slice(windowStart, windowEnd)",
  "data-windowed-eventlog",
  "data-rendered-count",
  "Turn from",
  "Turn to",
  "Event type",
  "Actor",
  "Tags"
];

for (const token of requiredWindowingTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing EventLog windowing/filter token: ${token}`);
}

if (panelSource.includes("filteredEvents.map(")) {
  failures.push("EventLogViewerPanel still maps all filtered events instead of only the visible window.");
}

if (!panelSource.includes("visibleEvents.map(")) {
  failures.push("EventLogViewerPanel does not render the visible event window.");
}

const cardStart = appSource.indexOf("function EventLogSafeCard");
const cardEnd = appSource.indexOf("function sortedUnique", cardStart);
const cardSource = cardStart >= 0 && cardEnd > cardStart ? appSource.slice(cardStart, cardEnd) : "";
if (!cardSource.includes("DebugGate")) failures.push("EventLog raw details are not clearly DebugGate-wrapped.");
if (/JSON\.stringify\(event/.test(cardSource) && !cardSource.includes("redactDebugText(event)")) {
  failures.push("EventLog debug detail does not use redacted debug text.");
}

if (!styleSource.includes(".eventlog-window-toolbar")) {
  failures.push("Missing EventLog window toolbar styles.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in EventLog UI source.");
}

if (failures.length) {
  console.error("v3.6 EventLog windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 EventLog windowing check passed.");
