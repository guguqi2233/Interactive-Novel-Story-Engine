import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src/api.ts"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");

const requiredAppTokens = [
  "Local Launcher / Startup Status",
  "Project Selector",
  "Recent Projects",
  "Local Config Wizard",
  "Provider Setup Wizard",
  "Desktop Health Check",
  "One-Click Quality Gate",
  "Backup / Restore Wizard",
  "Error Recovery Wizard",
  "Local Log Viewer",
  "Diagnostics Bundle UI",
  "Offline Help Center",
  "Settings / Preferences Sections",
  "First-Run Onboarding",
  "SafePathSummary",
  "No account needed",
  "No cloud sync",
  "No online marketplace",
  "API keys stay local",
  "Nothing is uploaded",
  "Mature Module default off"
];

const requiredCompletionTokens = [
  "Retry Health Check",
  "Open Local Config Wizard",
  "View Local Logs",
  "SQLite / Database",
  "Workspace",
  "Logs",
  "Workspace root",
  "Log directory",
  "Backup directory",
  "Privacy defaults",
  "safe provider status",
  "Explicit Confirm Create Backup",
  "Restore Dry-Run Preview",
  "Restart backend/frontend",
  "Reload project summary",
  "Level filter",
  "Component filter",
  "Last run summary",
  "Project id",
  "Mode status",
  "Pin",
  "Desktop Packaging"
];

const requiredApiTokens = [
  "fetchLocalStudioStatus",
  "fetchLocalStudioConfigSummary",
  "fetchLocalStudioStartupChecks",
  "createBackupDryRun",
  "restoreBackupDryRun",
  "fetchRecoveryIssues",
  "fetchLocalLogs",
  "previewDiagnosticsBundle"
];

const failures = [];

for (const token of requiredAppTokens) {
  if (!app.includes(token)) failures.push(`Missing v3.0 UX token: ${token}`);
}

for (const token of requiredCompletionTokens) {
  if (!app.includes(token)) failures.push(`Missing v3.0 completion token: ${token}`);
}

for (const token of requiredApiTokens) {
  if (!api.includes(token)) failures.push(`Missing v3.0 API helper: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(app) || /api_key:\s*["'][^"']+/i.test(app)) {
  failures.push("Plaintext api_key input or literal detected.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(app + api)) {
  failures.push("Secret-looking sk-* token detected in frontend source.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(app)) failures.push("Account/cloud/marketplace appears as a primary UI entry.");
}

if (!/"check:v30-ux"/.test(pkg)) failures.push("package.json is missing check:v30-ux.");

if (failures.length) {
  console.error("v3.0 Local Studio UX safety check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.0 Local Studio UX safety check passed.");
