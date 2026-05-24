import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styleSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function ProviderConnectivityDashboard");
const panelEnd = appSource.indexOf("function buildProviderConnectivityRow", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("ProviderConnectivityDashboard source slice not found.");

const requiredTokens = [
  "modelSearch",
  "modelCapabilityFilter",
  "modelEnabledFilter",
  "modelUseCaseFilter",
  "modelPageSize",
  "modelPageIndex",
  "visibleModelRows",
  "filteredModelRows.slice(modelWindowStart, modelWindowEnd)",
  "capabilityBadgesByModelId",
  "data-windowed-provider-model-list",
  "supports_text",
  "supports_json",
  "supports_streaming",
  "supports_tools",
  "Use case"
];

for (const token of requiredTokens) {
  if (!panelSource.includes(token)) failures.push(`Missing Provider model list windowing/filter token: ${token}`);
}

if (panelSource.includes("filteredModelRows.map(")) {
  failures.push("Provider model list still maps all filtered models instead of only the visible window.");
}

if (!panelSource.includes("visibleModelRows.map(")) {
  failures.push("Provider model list does not render the visible model window.");
}

const builderStart = appSource.indexOf("function buildProviderModelListRows");
const builderEnd = appSource.indexOf("function formatDuration", builderStart);
const builderSource = builderStart >= 0 && builderEnd > builderStart ? appSource.slice(builderStart, builderEnd) : "";
if (!builderSource.includes("ProviderModelListRow")) failures.push("Provider model rows are not normalized into ProviderModelListRow.");
if (!builderSource.includes("redactReportText")) failures.push("Provider model rows are not redacted.");
if (!builderSource.includes("providerCapabilityFlag")) failures.push("Provider capability flags are not normalized safely.");

if (!appSource.includes("ProviderCapabilityMatrixPanel")) {
  failures.push("Prompt Lab capability matrix summary panel is missing.");
}

for (const cssToken of [".provider-model-list", ".provider-model-window", ".provider-model-row", ".provider-model-capability-badges"]) {
  if (!styleSource.includes(cssToken)) failures.push(`Missing Provider model list style token: ${cssToken}`);
}

if (/JSON\.stringify\([^)]*provider/i.test(panelSource) || /SafeJSON value=\{provider/i.test(panelSource)) {
  failures.push("Provider model list panel appears to render raw provider response JSON.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in Provider UI source.");
}

if (failures.length) {
  console.error("v3.6 Provider model list windowing check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Provider model list windowing check passed.");
