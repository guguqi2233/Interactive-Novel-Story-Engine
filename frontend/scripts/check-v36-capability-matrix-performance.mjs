import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function ProviderCapabilityMatrixPanel");
const panelEnd = appSource.indexOf("function ProviderConnectivityDashboard", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("ProviderCapabilityMatrixPanel source slice not found.");

for (const token of [
  "matrixSafeSummary",
  "buildProviderCapabilityMatrixSafeSummary",
  "providerFilter",
  "capabilityFilter",
  "useCaseFilter",
  "matrixPageSize",
  "matrixPageIndex",
  "visibleMatrixRows",
  "filteredMatrixRows.slice(matrixWindowStart, matrixWindowEnd)",
  "collapsedMatrixProviders",
  "warningSummaryByRowId",
  "data-windowed-capability-matrix",
  "Raw provider metadata and API keys are not rendered"
]) {
  if (!panelSource.includes(token)) failures.push(`Missing capability matrix performance token: ${token}`);
}

if (panelSource.includes("filteredMatrixRows.map(")) {
  failures.push("Capability matrix panel renders all filtered rows instead of only the visible window.");
}

if (!panelSource.includes("visibleMatrixRows.length")) {
  failures.push("Capability matrix panel does not expose visible row count.");
}

const builderStart = appSource.indexOf("function buildProviderCapabilityMatrixSafeSummary");
const builderEnd = appSource.indexOf("function buildProviderConnectivityRow", builderStart);
const builderSource = builderStart >= 0 && builderEnd > builderStart ? appSource.slice(builderStart, builderEnd) : "";
for (const token of ["redactReportText", "providerCapabilityFlag", "disabledReasons", "warningCount", "blockerCount", "groupCapabilityMatrixRowsByProvider"]) {
  if (!builderSource.includes(token)) failures.push(`Missing capability matrix safe summary token: ${token}`);
}

for (const cssToken of [".capability-matrix-panel", ".capability-matrix-window", ".capability-matrix-provider-group", ".capability-matrix-row"]) {
  if (!styleSource.includes(cssToken)) failures.push(`Missing capability matrix style token: ${cssToken}`);
}

if (/SafeJSON value=\{providerCapabilityMatrix/i.test(appSource) || /JSON\.stringify\([^)]*providerCapabilityMatrix/i.test(appSource)) {
  failures.push("Capability matrix appears to render raw provider metadata JSON.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in capability matrix UI source.");
}

if (failures.length) {
  console.error("v3.6 Capability matrix performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Capability matrix performance check passed.");
