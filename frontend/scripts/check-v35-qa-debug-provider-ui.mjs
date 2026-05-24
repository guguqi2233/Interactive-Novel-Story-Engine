import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

function readTree(dir) {
  let text = "";
  for (const entry of readdirSync(dir)) {
    const full = resolve(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) text += readTree(full);
    else if (/\.(tsx?|mjs)$/.test(entry)) text += `\n/* ${full} */\n${readFileSync(full, "utf8")}`;
  }
  return text;
}

const source = readTree(resolve(root, "src"));
const scripts = readTree(resolve(root, "scripts"));
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const requiredUiTokens = [
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
  "UnifiedQualityGateDashboard",
  "Quality Gate Unified Dashboard Pro",
  "PerformanceDashboard",
  "ProviderConnectivityDashboard",
  "Provider Connectivity Dashboard",
  "Provider Model Assignment by Mode",
  "ProviderUsageCostDashboard",
  "Provider Usage / Cost Dashboard Pro",
  "CrossModeConflictReviewPro",
  "CrossMode Conflict Review Pro",
  "ModulePlaytestStressProPanel",
  "Module Playtest / Stress UI Pro",
  "Save Migration Visualizer",
  "Diagnostics Bundle Review UI",
  "SafeDebugExportWizard",
  "Safe Debug Export Wizard",
  "SafeDebugNotice",
  "EventTypeBadge",
  "StateDeltaOpBadge",
  "QualitySeverityBadge",
  "LeakRiskBadge",
  "ProviderConnectionStatusBadge",
  "ModelCapabilityBadge",
  "TestRunStatusBadge",
  "RedactedValue",
  "SafeReportCard",
  "FilterToolbar"
];

for (const token of requiredUiTokens) {
  if (!source.includes(token)) failures.push(`Missing v3.5 QA/Debug/Provider UI token: ${token}`);
}

if (!source.includes("Performance Dashboard Pro") && !source.includes("Local Performance Dashboard Polish")) {
  failures.push("Missing v3.5/v3.6 Performance Dashboard title token.");
}

const requiredSafetyCopy = [
  "ENABLE_DEBUG_API",
  "DebugGate",
  "raw StateDelta",
  "debug-gated",
  "API keys",
  "provider secrets",
  "raw env",
  "Authorization header",
  "transient_api_key",
  "fake provider or fake client",
  "CI must not call real providers",
  "No arbitrary command UI",
  "No generic terminal",
  "no custom shell input",
  "No upload was performed",
  "local-only"
];

for (const token of requiredSafetyCopy) {
  if (!source.includes(token) && !scripts.includes(token)) failures.push(`Missing v3.5 safety/local-first copy: ${token}`);
}

const debugSensitiveFunctions = [
  "function StateDeltaViewerPanel",
  "function VisibleDebugStateCompare",
  "function GameplayModuleDebugger",
  "function TimelineEventCard"
];

for (const fn of debugSensitiveFunctions) {
  const start = source.indexOf(fn);
  if (start < 0) {
    failures.push(`Missing debug-sensitive component: ${fn}`);
    continue;
  }
  const nextFunction = source.indexOf("\nfunction ", start + fn.length);
  const slice = source.slice(start, nextFunction > start ? nextFunction : start + 6000);
  if (!slice.includes("DebugGate") && !slice.includes("ENABLE_DEBUG_API required")) {
    failures.push(`${fn} is not clearly debug gated.`);
  }
}

const normalUiSlices = [
  ["ProviderConnectivityDashboard", "function ProviderConnectivityDashboard"],
  ["ProviderUsageCostDashboard", "function ProviderUsageCostDashboard"],
  ["HiddenLeakReportPanel", "function HiddenLeakReportPanel"],
  ["ModulePlaytestStressProPanel", "function ModulePlaytestStressProPanel"],
  ["DiagnosticsBundlePanel", "function DiagnosticsBundlePanel"],
  ["LocalTestRunDashboard", "function LocalTestRunDashboard"],
  ["SafeDebugExportWizard", "function SafeDebugExportWizard"]
];

for (const [name, marker] of normalUiSlices) {
  const start = source.indexOf(marker);
  if (start < 0) {
    failures.push(`Missing normal UI slice: ${name}`);
    continue;
  }
  const nextFunction = source.indexOf("\nfunction ", start + marker.length);
  const slice = source.slice(start, nextFunction > start ? nextFunction : start + 7000);
  if (/JSON\.stringify\([^)]*state_delta/i.test(slice)) failures.push(`${name} renders raw state_delta JSON.`);
  if (/<pre>/i.test(slice) && !slice.includes("DebugGate")) failures.push(`${name} renders a raw <pre> outside DebugGate.`);
  if (/(api_key\s*[:=]\s*["'][^"']+|authorization\s*[:=]\s*["'][^"']+)/i.test(slice)) failures.push(`${name} contains plaintext secret-looking literal.`);
}

if (/<input[^>]+name=["']api_key["']/i.test(source) || /api_key:\s*["'][^"']+/i.test(source)) {
  failures.push("Plaintext api_key input or literal detected in frontend source.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(source + scripts)) {
  failures.push("Secret-looking sk-* token detected in frontend files.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download|Online Play)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download|Online Play)\s*<\/h[1-6]>/i,
  /arbitrary command input/i,
  /generic terminal/i,
  /custom shell input/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(source) && !source.includes("No arbitrary command input or terminal is exposed.")) {
    failures.push("Account/cloud/online marketplace/remote download/arbitrary shell UI appears as a primary enabling surface.");
  }
}

if (!/"check:v35-qa-debug-provider-ui"/.test(pkg)) failures.push("package.json is missing check:v35-qa-debug-provider-ui.");

if (failures.length) {
  console.error("v3.5 QA / Debug / Provider UI regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.5 QA / Debug / Provider UI regression check passed.");
