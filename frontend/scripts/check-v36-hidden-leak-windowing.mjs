import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function HiddenLeakReportPanel");
const panelEnd = appSource.indexOf("function buildHiddenLeakIssues", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("HiddenLeakReportPanel source slice not found.");

const requiredTokens = [
  "HIDDEN_LEAK_TARGETS",
  "targetGroup",
  "severityFilter",
  "sourceTargetFilter",
  "issueSearch",
  "pageSize",
  "pageIndex",
  "visibleIssues",
  "filteredIssues.slice(windowStart, windowEnd)",
  "collapsedTargets",
  "data-windowed-hidden-leak-report",
  "Safe metadata search",
  "Source / target"
];

for (const token of requiredTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing Hidden Leak windowing/filter token: ${token}`);
}

for (const target of ["UI", "prompt", "export", "diagnostics", "backup", "logs"]) {
  if (!appSource.includes(`"${target}"`)) failures.push(`Missing leak target group: ${target}`);
}

if (panelSource.includes("filteredIssues.map(")) {
  failures.push("HiddenLeakReportPanel still maps all filtered issues instead of only the visible window.");
}

if (!panelSource.includes("visibleIssues.filter(") || !panelSource.includes("targetIssues.map(")) {
  failures.push("HiddenLeakReportPanel does not render grouped visible leak issues.");
}

const builderStart = appSource.indexOf("function hiddenLeakIssue");
const builderEnd = appSource.indexOf("function collectLeakStrings", builderStart);
const builderSource = builderStart >= 0 && builderEnd > builderStart ? appSource.slice(builderStart, builderEnd) : "";
if (!builderSource.includes("redactLeakSummary(summary)")) failures.push("Hidden leak summaries are not redacted at issue creation.");
if (!builderSource.includes("inferHiddenLeakTarget")) failures.push("Hidden leak issues do not infer safe target groups.");

for (const cssToken of [".hidden-leak-issue-browser", ".hidden-leak-target-group", ".hidden-leak-target-toggle", ".hidden-leak-issue-row"]) {
  if (!styleSource.includes(cssToken)) failures.push(`Missing Hidden Leak style token: ${cssToken}`);
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in Hidden Leak UI source.");
}

if (failures.length) {
  console.error("v3.6 Hidden Leak windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Hidden Leak windowing check passed.");
