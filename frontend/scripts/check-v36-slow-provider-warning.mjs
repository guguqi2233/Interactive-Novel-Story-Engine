import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function SlowProviderWarningPanel");
const panelEnd = appSource.indexOf("function buildProviderCapabilityMatrixSafeSummary", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("SlowProviderWarningPanel source slice not found.");

for (const [token, label] of [
  ["data-v36-slow-provider-warning", "slow provider check marker"],
  ["Slow Provider Warning UI", "panel title"],
  ["PROVIDER_HIGH_LATENCY_MS", "high latency threshold"],
  ["PROVIDER_TIMEOUT_REPEAT_COUNT", "repeated timeout threshold"],
  ["PROVIDER_HIGH_ERROR_RATE", "high error rate threshold"],
  ["high_latency", "high latency warning kind"],
  ["repeated_timeout", "repeated timeout warning kind"],
  ["model_list_slow", "model list slow warning kind"],
  ["high_error_rate", "high error rate warning kind"],
  ["check base URL", "base URL suggestion"],
  ["check local model service", "local model service suggestion"],
  ["check provider status", "provider status suggestion"],
  ["use another model/fallback", "fallback suggestion"],
  ["increase timeout cautiously", "timeout suggestion"],
  ["No prompt/output text", "prompt/output exclusion wording"],
  ["raw provider error", "raw provider error exclusion wording"],
  ["API key", "API key exclusion wording"],
  ["buildSlowProviderWarnings", "warning builder"],
  ["usageSummary.latency_p95_ms", "usage latency detection"],
  ["row.connectionStatus === \"timeout\"", "timeout status detection"],
  ["row.connectionStatus === \"model_list_failed\"", "model list failed detection"],
  ["usageSummary.error_rate", "high error rate detection"],
  ["redactReportText(safeSummary)", "safe summary redaction"]
]) {
  if (!appSource.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

if (!appSource.includes("usageSummary={projectUsageSummary}") || !appSource.includes("recentUsage={projectRecentUsage}")) {
  failures.push("ProviderConnectivityDashboard is not wired to project usage safe summaries.");
}

if (/raw[_ -]?provider[_ -]?error[^.]*\{/.test(panelSource)) {
  failures.push("Slow provider panel appears to render raw provider error data.");
}

if (/SafeJSON|<pre>|prompt\s*[:=]|output\s*[:=]|Authorization\s*[:=]|transient_api_key\s*[:=]/i.test(panelSource)) {
  failures.push("Slow provider panel contains risky raw JSON, prompt/output, auth, or transient token rendering pattern.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource)) {
  failures.push("Secret-looking sk-* token detected in Provider UI source.");
}

if (!/"check:v36-slow-provider-warning"/.test(pkg)) {
  failures.push("package.json is missing check:v36-slow-provider-warning.");
}

if (failures.length) {
  console.error("v3.6 Slow Provider Warning UI check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Slow Provider Warning UI check passed.");
