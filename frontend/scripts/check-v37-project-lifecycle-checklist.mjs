import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 14000);
}

requireToken(desktopUi, "function LocalProjectLifecycleChecklist", "Local Project Lifecycle Checklist component");
requireToken(desktopUi, "data-v37-project-lifecycle-checklist=\"safe-summary\"", "safe summary marker");
requireToken(desktopUi, "buildLocalProjectLifecycleItems", "lifecycle item builder");
requireToken(desktopUi, "safePathSummaries", "safe path summary helper");
requireToken(desktopUi, "redactLifecycleText", "lifecycle redaction helper");
requireToken(desktopUi, "No project selected yet; use Project Home or Project Picker to create/open one.", "no project empty state");
requireToken(desktopUi, "A local project/workspace is selected.", "project ready state");
requireToken(desktopUi, "Backup missing warning", "backup missing warning copy");
requireToken(desktopUi, "Diagnostics safe warning", "diagnostics safe warning copy");
requireToken(desktopUi, "do not upload data", "no upload boundary copy");
requireToken(desktopUi, "do not call real providers", "no real provider boundary copy");
requireToken(desktopUi, "do not read arbitrary files from the UI", "no arbitrary file read boundary copy");
requireToken(styles, ".lifecycle-safe-path-summary", "lifecycle safe path styles");

for (const label of [
  "Create project",
  "Open project",
  "Recent projects",
  "Project health check",
  "Project settings",
  "Provider settings",
  "Quality Gate",
  "Backup",
  "Restore dry-run",
  "Diagnostics preview",
  "Export",
  "Safe path summary",
  "Local privacy notice"
]) {
  requireToken(desktopUi, label, `${label} lifecycle checklist item`);
}

const lifecycleComponent = sourceSlice(desktopUi, "function LocalProjectLifecycleChecklist", "function buildLocalProjectLifecycleItems");
const lifecycleBuilder = sourceSlice(desktopUi, "function buildLocalProjectLifecycleItems", "function lifecycleItem");
const lifecycleSource = `${lifecycleComponent}\n${lifecycleBuilder}`;

if (lifecycleSource.includes("fetch(") || lifecycleSource.includes("requestJson") || lifecycleSource.includes("testProjectProviderConnection")) {
  failures.push("Lifecycle checklist must be read-only and must not call backend/provider APIs directly.");
}
if (lifecycleSource.includes("createLocalBackup(") || lifecycleSource.includes("restoreBackupDryRun(") || lifecycleSource.includes("createDiagnosticsBundle(")) {
  failures.push("Lifecycle checklist should show status and jump links, not run backup/restore/diagnostics actions.");
}
if (lifecycleSource.includes("saveGame(") || lifecycleSource.includes("submitPlayerInput(") || lifecycleSource.includes("applyStateDelta")) {
  failures.push("Lifecycle checklist must not modify GameState or apply state deltas.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(lifecycleSource)) {
  failures.push("Secret-looking sk-* token detected in lifecycle checklist source.");
}
if (/[A-Z]:\\(?:Users|KF|world|[^"'<>\\]+\\)/.test(lifecycleComponent)) {
  failures.push("Raw Windows path literal detected in rendered lifecycle checklist component.");
}
if (/<input[^>]+(api_key|secret|transient)/i.test(lifecycleSource)) {
  failures.push("Lifecycle checklist must not render plaintext secret inputs.");
}

if (!pkg.scripts?.["check:v37-project-lifecycle"]) {
  failures.push("package.json is missing check:v37-project-lifecycle.");
}

if (failures.length) {
  console.error("v3.7 project lifecycle checklist check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 project lifecycle checklist check passed.");
