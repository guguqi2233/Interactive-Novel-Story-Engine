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
  return source.slice(start, end > start ? end : start + 32000);
}

requireToken(desktopUi, "function ProductAcceptanceChecklistPanel", "Product Acceptance Checklist UI component");
requireToken(desktopUi, "Product Acceptance Checklist UI", "acceptance checklist title");
requireToken(desktopUi, "v3.7 Product Acceptance Checklist", "acceptance checklist heading");
requireToken(desktopUi, "Run readiness check", "manual readiness check button");
requireToken(desktopUi, "Jump to issue", "jump to issue button");
requireToken(desktopUi, "buildProductAcceptanceChecklistItems", "acceptance checklist builder");
requireToken(desktopUi, "normalizeAcceptanceStatus", "acceptance status normalization");
requireToken(desktopUi, "safe-summary only", "safe summary wording");
requireToken(desktopUi, "never uploads data or calls a real provider", "no upload/no real provider wording");

for (const category of [
  "Project lifecycle",
  "Provider setup",
  "Novel workflow",
  "Tavern workflow",
  "World workflow",
  "Cross-Mode workflow",
  "Authoring / Mod workflow",
  "QA / Debug / Replay workflow",
  "Backup / Restore / Diagnostics workflow",
  "Export workflow",
  "Privacy / Secrets",
  "Documentation"
]) {
  requireToken(desktopUi, `"${category}"`, `${category} acceptance category`);
}

for (const status of [
  "\"ready\"",
  "\"warning\"",
  "\"missing\""
]) {
  requireToken(desktopUi, status, `${status} acceptance status`);
}

const panel = sourceSlice(desktopUi, "function ProductAcceptanceChecklistPanel", "function LocalProjectLifecycleChecklist");
for (const forbidden of [
  "testProjectProviderConnection",
  "fetchProjectProviderStatus",
  "fetch(",
  "requestJson",
  "createDiagnosticsBundle(",
  "createBackup(",
  "setGameState",
  "applyStateDelta",
  "localStorage.setItem",
  "sessionStorage.setItem",
  "sk-",
  "Authorization:"
]) {
  if (panel.includes(forbidden)) {
    failures.push(`Acceptance checklist panel includes forbidden active call or secret-like token: ${forbidden}`);
  }
}

requireToken(styles, ".product-acceptance-checklist", "acceptance checklist style");

if (!pkg.scripts?.["check:v37-product-acceptance"]) {
  failures.push("package.json is missing check:v37-product-acceptance.");
}

if (failures.length) {
  console.error("v3.7 product acceptance checklist check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product acceptance checklist check passed.");
