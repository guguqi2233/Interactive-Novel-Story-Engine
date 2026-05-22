import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src/api.ts"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");

const requiredAppCopy = [
  "UnifiedNavigation",
  "LocalStatusBar",
  "DiagnosticsExportPanel",
  "Local Help / Onboarding",
  "Project Home",
  "Novel Studio",
  "Tavern Studio",
  "World Studio",
  "Cross-Mode Bridge",
  "Script / Mod Platform Pro",
  "Provider Setup",
  "Quality Gate Dashboard",
  "No cloud sync",
  "No online marketplace",
  "API keys are not stored in project",
  "Debug / Replay",
  "Mature Module is disabled by default",
  "Export local diagnostics JSON"
];

const requiredApiHelpers = [
  "class ApiError",
  "safeFetch",
  "parseJsonSafe",
  "getErrorMessageSafe",
  "isApiDisabledError",
  "isDebugDisabledError"
];

const failures = [];

for (const token of requiredAppCopy) {
  if (!app.includes(token)) {
    failures.push(`Missing v2.9 UI token: ${token}`);
  }
}

for (const token of requiredApiHelpers) {
  if (!api.includes(token)) {
    failures.push(`Missing safe API helper: ${token}`);
  }
}

if (/<input[^>]+name=["']api_key["']/i.test(app) || /api_key:\s*["'][^"']+/i.test(app)) {
  failures.push("Plaintext api_key input or literal detected in App.tsx.");
}

if (/name=["']api_key_env["']/i.test(app)) {
  failures.push("api_key_env should be a safe provider reference, not a raw api_key field.");
}

if (/sk-[A-Za-z0-9_-]{8,}/.test(app + api)) {
  failures.push("Secret-looking sk-* token detected in frontend source.");
}

const forbiddenNearTermEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenNearTermEntrypoints) {
  if (pattern.test(app)) {
    failures.push("Account/cloud/marketplace appears as a primary UI entry.");
  }
}

if (/online marketplace/i.test(app) && !/No online marketplace/i.test(app)) {
  failures.push("Online marketplace copy is present without local-only exclusion.");
}

if (/remote auto-download/i.test(app) && !/no remote auto-download/i.test(app)) {
  failures.push("Remote package download copy is present without local-only exclusion.");
}

if (/raw state_deltas/i.test(app) && !/Debug \/ Replay/i.test(app)) {
  failures.push("raw state_deltas copy must remain tied to debug/replay guidance.");
}

if (!/"check:v29-ui"/.test(pkg)) {
  failures.push("package.json is missing check:v29-ui script.");
}

if (failures.length) {
  console.error("v2.9 UI safety check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v2.9 UI safety check passed.");
