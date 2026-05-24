import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function TimelineReplayPanel");
const panelEnd = appSource.indexOf("function ReplaySummaryView", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("TimelineReplayPanel source slice not found.");

const requiredWindowingTokens = [
  "visibleReplayEvents",
  "turnWindowSize",
  "turnPageIndex",
  "windowedTurns",
  "data-windowed-timeline",
  "data-rendered-turn-count",
  "data-rendered-event-count",
  "Jump to turn",
  "Turn from",
  "Turn to",
  "Event type",
  "activeEventId",
  "selectActiveEvent"
];

for (const token of requiredWindowingTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing Timeline Replay windowing token: ${token}`);
}

if (panelSource.includes("filteredTurns.map(")) {
  failures.push("TimelineReplayPanel still maps all filtered turn groups instead of only the visible window.");
}

if (!panelSource.includes("windowedTurns.map(")) {
  failures.push("TimelineReplayPanel does not render the windowed turn groups.");
}

const cardStart = appSource.indexOf("function TimelineEventCard");
const cardEnd = appSource.indexOf("function filterTimelineTurns", cardStart);
const cardSource = cardStart >= 0 && cardEnd > cardStart ? appSource.slice(cardStart, cardEnd) : "";
if (!cardSource.includes("active")) failures.push("TimelineEventCard does not expose active event highlighting.");
if (!cardSource.includes("DebugGate")) failures.push("TimelineEventCard debug details are not clearly DebugGate-wrapped.");
if (!cardSource.includes("timelineEventSafeSummary")) failures.push("TimelineEventCard does not use a safe normal replay summary.");
if (!cardSource.includes("data-timeline-redacted-normal-summary")) failures.push("TimelineEventCard normal summary is not explicitly marked as redacted.");
if (cardSource.includes("<span>{event.result}</span>")) failures.push("TimelineEventCard renders raw event result in the normal summary.");
if (cardSource.includes("<span>{event.action_type}</span>")) failures.push("TimelineEventCard renders raw action_type in the normal summary.");
if (cardSource.includes("<span>{event.actor_id}</span>")) failures.push("TimelineEventCard renders raw actor_id in the normal summary.");
if (/JSON\.stringify\(event\.state_deltas/.test(cardSource)) {
  failures.push("TimelineEventCard renders raw state_deltas without redaction.");
}
if (!cardSource.includes("redactDebugText(event.state_deltas)")) {
  failures.push("TimelineEventCard does not redact debug StateDelta details.");
}

const safeHelpersStart = appSource.indexOf("function timelineEventSafeSummary");
const safeHelpersEnd = appSource.indexOf("function filterTimelineTurns", safeHelpersStart);
const safeHelpersSource = safeHelpersStart >= 0 && safeHelpersEnd > safeHelpersStart ? appSource.slice(safeHelpersStart, safeHelpersEnd) : "";
if (!safeHelpersSource.includes("Hidden/debug summary is redacted from normal replay view.")) {
  failures.push("Timeline Replay safe helper does not redact non-visible event summaries.");
}

if (!styleSource.includes(".timeline-window-toolbar")) {
  failures.push("Missing Timeline Replay window toolbar styles.");
}
if (!styleSource.includes(".replay-event.active")) {
  failures.push("Missing active replay event style.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in Timeline Replay UI source.");
}

if (failures.length) {
  console.error("v3.6 Timeline Replay windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Timeline Replay windowing check passed.");
