import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 20000);
}

requireToken(app, "function UnifiedNavigation", "UnifiedNavigation component");
requireToken(app, "product-nav-status", "current local product status summary");
requireToken(app, "Current local product status", "status aria label");
requireToken(app, "Local studio navigation", "main navigation aria label");
requireToken(app, "aria-current={item.active ? \"page\" : undefined}", "current mode highlight");
requireToken(app, "Debug API disabled by ENABLE_DEBUG_API", "debug gated tooltip");
requireToken(app, "No account, no cloud sync, no online marketplace.", "local-only nav note");

for (const label of [
  "Project",
  "Novel",
  "Tavern",
  "World",
  "Cross-Mode",
  "Authoring / Mods",
  "Provider",
  "QA / Quality",
  "Settings",
  "Backup",
  "Diagnostics"
]) {
  requireToken(app, `label: "${label}"`, `${label} navigation entry`);
}
requireToken(app, "<span>Debug / Replay</span>", "Debug / Replay navigation entry");

for (const token of [
  "Create/Open Project",
  "Provider setup needed",
  "Run Quality Gate",
  "Next action: configure a local Provider profile or local_stub.",
  "Next action: run a backup dry-run before creating a backup.",
  "Next action: preview diagnostics locally before creating a bundle.",
  "Gated"
]) {
  requireToken(app, token, `${token} navigation next-action/status copy`);
}

const navigation = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
for (const forbidden of [
  "Create Account",
  "Cloud Sync",
  "Online Marketplace",
  "Remote Package Download",
  "Upload Project",
  "api_key",
  "transient_api_key",
  "raw_state_delta",
  "hidden fact text"
]) {
  if (navigation.includes(forbidden)) {
    failures.push(`Navigation includes forbidden main-entry or sensitive token: ${forbidden}`);
  }
}

requireToken(styles, ".unified-navigation", "navigation styles");
requireToken(styles, ".product-nav-status", "product nav status styles");
requireToken(styles, ".nav-item.active", "active nav item style");
requireToken(styles, ".nav-item.debug-gated .nav-badge", "debug gated badge style");
requireToken(styles, ".sr-only", "screen-reader-only helper");

if (!pkg.scripts?.["check:v37-product-navigation"]) {
  failures.push("package.json is missing check:v37-product-navigation.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(navigation)) {
  failures.push("Secret-looking sk-* token detected in navigation source.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|CloudBackup|OnlineDiagnosticsUpload)/i.test(navigation)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected in navigation source.");
}
if (/setGameState|applyStateDelta|submitPlayerInput|testProjectProviderConnection/.test(navigation)) {
  failures.push("Navigation must not directly modify GameState or test providers.");
}

if (failures.length) {
  console.error("v3.7 product navigation check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product navigation check passed.");
