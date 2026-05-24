import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function UnifiedQualityGateDashboard");
const panelEnd = appSource.indexOf("function buildUnifiedQualityGateRows", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("UnifiedQualityGateDashboard source slice not found.");

const requiredTokens = [
  "categoryFilter",
  "severityFilter",
  "modeSourceFilter",
  "issueSearch",
  "pageSize",
  "pageIndex",
  "visibleIssues",
  "filteredIssues.slice(windowStart, windowEnd)",
  "collapsedCategories",
  "data-windowed-quality-report",
  "Issue Browser",
  "Mode / source",
  "Issue search"
];

for (const token of requiredTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing quality report optimization token: ${token}`);
}

if (panelSource.includes("filteredIssues.map(")) {
  failures.push("UnifiedQualityGateDashboard still maps all filtered issues instead of only the visible window.");
}

if (!panelSource.includes("visibleIssues.filter(") || !panelSource.includes("issues.map(")) {
  failures.push("UnifiedQualityGateDashboard does not render grouped visible issues.");
}

const builderStart = appSource.indexOf("function buildUnifiedQualityGateRows");
const builderEnd = appSource.indexOf("function WorldStudioLanding", builderStart);
const builderSource = builderStart >= 0 && builderEnd > builderStart ? appSource.slice(builderStart, builderEnd) : "";
if (!builderSource.includes("qualityIssue(")) failures.push("Quality rows are not normalized through qualityIssue safe summaries.");
if (!builderSource.includes("redactLeakSummary(safeSummary)")) failures.push("Quality issue summaries are not passed through leak redaction.");
if (!builderSource.includes("hidden_entities_redacted")) failures.push("Content coverage hidden entity redaction counts are not represented safely.");

for (const cssToken of [".quality-issue-browser", ".quality-category-group", ".quality-issue-row"]) {
  if (!styleSource.includes(cssToken)) failures.push(`Missing quality report style token: ${cssToken}`);
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in Quality Dashboard source.");
}

if (failures.length) {
  console.error("v3.6 Quality report windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Quality report windowing check passed.");
