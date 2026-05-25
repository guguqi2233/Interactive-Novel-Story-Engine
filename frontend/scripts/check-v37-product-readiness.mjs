import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 14000);
}

requireToken(app, "function ProductReadinessDashboard", "Product Readiness Dashboard component");
requireToken(app, "data-v37-product-readiness=\"safe-summary\"", "v3.7 safe summary marker");
requireToken(app, "type ProductReadinessStatus = \"ready\" | \"warning\" | \"missing\" | \"disabled\" | \"not checked\"", "readiness status union");
requireToken(app, "buildProductReadinessItems", "readiness item builder");
requireToken(app, "safeSummary", "safe summary field");
requireToken(app, "nextAction", "next action field");
requireToken(app, "jumpLabel", "jump link field");
requireToken(app, "Product readiness safe summaries never include API keys", "secret exclusion copy");

for (const label of [
  "Project status",
  "Provider setup status",
  "Model assignment status",
  "Novel readiness",
  "Tavern readiness",
  "World readiness",
  "Authoring / Mod readiness",
  "QA / Debug / Replay readiness",
  "Backup / Restore readiness",
  "Export / Diagnostics readiness",
  "Privacy / secrets readiness",
  "Documentation / guide readiness"
]) {
  requireToken(app, `label: "${label}"`, `${label} item`);
}

requireToken(app, "Missing provider setup warning", "missing provider warning copy");
requireToken(app, "Missing backup config warning", "missing backup config warning copy");
requireToken(app, "Open Provider Setup", "provider jump action");
requireToken(app, "Open Backup", "backup jump action");
requireToken(app, "Open Diagnostics", "diagnostics jump action");
requireToken(app, "redactReportText(item.safeSummary)", "safe summary redaction");
requireToken(app, "redactReportText(item.nextAction)", "next action redaction");

const dashboard = sourceSlice(app, "function ProductReadinessDashboard", "function NovelCompleteWorkflowChecklist");
if (dashboard.includes("transient_api_key") || dashboard.includes("raw provider response")) {
  failures.push("Product Readiness Dashboard component includes sensitive provider terms outside exclusion copy.");
}
if (dashboard.includes("fetch(") || dashboard.includes("requestJson") || dashboard.includes("testProjectProviderConnection")) {
  failures.push("Product Readiness Dashboard should aggregate existing local state, not call real provider/network APIs.");
}

const builder = sourceSlice(app, "function buildProductReadinessItems", "function productReadinessPillClass");
if (builder.includes("set") && /set[A-Z]\w+\(/.test(builder)) {
  failures.push("Product readiness builder appears to mutate React state.");
}
if (builder.includes("submitPlayerInput") || builder.includes("saveGame(") || builder.includes("applySaveMigration")) {
  failures.push("Product readiness builder must not modify GameState or apply deltas.");
}

requireToken(styles, ".product-readiness-dashboard", "dashboard styles");
requireToken(styles, ".product-readiness-item", "readiness item styles");
requireToken(styles, ".product-readiness-item.missing", "missing status style");

if (!pkg.scripts?.["check:v37-product-readiness"]) {
  failures.push("package.json is missing check:v37-product-readiness.");
}

const sourceBundle = `${app}\n${styles}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(sourceBundle)) {
  failures.push("Secret-looking sk-* token detected in v3.7 frontend source.");
}
if (/<input[^>]+name=["']api_key["']/i.test(sourceBundle)) {
  failures.push("Plaintext api_key input detected in frontend UI.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i.test(sourceBundle)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected.");
}

if (failures.length) {
  console.error("v3.7 product readiness check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product readiness check passed.");
