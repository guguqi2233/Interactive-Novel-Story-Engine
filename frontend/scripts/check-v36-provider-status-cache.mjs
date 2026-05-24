import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const apiSource = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const backendCacheSource = readFileSync(resolve(root, "..", "backend", "app", "llm", "provider_connection_cache.py"), "utf8");
const failures = [];

const panelStart = appSource.indexOf("function ProviderConnectivityDashboard");
const panelEnd = appSource.indexOf("function buildProviderConnectivityRow", panelStart);
const panelSource = panelStart >= 0 && panelEnd > panelStart ? appSource.slice(panelStart, panelEnd) : "";

if (!panelSource) failures.push("ProviderConnectivityDashboard source slice not found.");

for (const token of [
  "Stale provider status cache",
  "No background provider call is made",
  "Cache state",
  "Latency",
  "Safe error type",
  "onTestConnection"
]) {
  if (!panelSource.includes(token)) failures.push(`Missing provider status cache UI token: ${token}`);
}

for (const token of ["refreshProviderConnection", "testProjectProviderConnection", "cache_state", "stale"]) {
  if (!appSource.includes(token)) failures.push(`Missing provider status cache integration token: ${token}`);
}

if (!apiSource.includes("ProviderConnectionStatus") || !apiSource.includes("/providers/test-connection")) {
  failures.push("Provider connection test API client is missing.");
}

const allowedCacheFields = [
  "provider_profile_id",
  "status",
  "tested_at",
  "latency_ms",
  "safe_error_type",
  "model_count",
  "redaction_applied"
];
for (const field of allowedCacheFields) {
  if (!backendCacheSource.includes(field)) failures.push(`Missing safe cache field: ${field}`);
}

for (const forbidden of ["safe_message", "Authorization header", "raw provider response", "raw error body", "transient_api_key"]) {
  if (!backendCacheSource.toLowerCase().includes(forbidden.toLowerCase())) {
    failures.push(`Provider cache source does not explicitly exclude: ${forbidden}`);
  }
}

const persistPattern = /(safe_message|authorization|raw_provider_response|transient_api_key)\s*[:=]/i;
if (persistPattern.test(backendCacheSource)) {
  failures.push("Provider cache source appears to persist forbidden provider data.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(appSource) || /sk-[A-Za-z0-9_-]{12,}/.test(apiSource)) {
  failures.push("Secret-looking sk-* token detected in frontend provider status cache code.");
}

if (failures.length) {
  console.error("v3.6 Provider connection status cache check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Provider connection status cache check passed.");
