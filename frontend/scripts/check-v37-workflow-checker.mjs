import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const backendWorkflow = readFileSync(resolve(root, "..", "backend", "app", "platform", "product_workflow.py"), "utf8");
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

requireToken(api, "export type ProductWorkflowCheckReport", "workflow report API type");
requireToken(api, "/projects/${encodeURIComponent(projectId)}/workflow-check", "workflow check API route");
requireToken(app, "fetchProjectWorkflowCheck", "workflow check API import/use");
requireToken(app, "workflowCheckReport", "workflow check state");
requireToken(app, "workflowCheckError", "workflow check error state");
requireToken(app, "refreshWorkflowCheck", "workflow refresh function");
requireToken(desktopUi, "function WorkflowCheckPanel", "WorkflowCheckPanel component");
requireToken(desktopUi, "End-to-End Local Workflow Checker", "workflow checker title");
requireToken(desktopUi, "Read-only checklist", "read-only workflow copy");
requireToken(desktopUi, "Run workflow check", "manual workflow refresh action");
requireToken(desktopUi, "Workflow check responses never include API keys", "secret exclusion copy");
requireToken(pkg.scripts?.["check:v37-workflow-checker"] ?? "", "node scripts/check-v37-workflow-checker.mjs", "package script");

for (const label of [
  "Project created/opened",
  "Provider configured",
  "Connection status checked",
  "Model list available or manual model configured",
  "Model assignment complete",
  "Novel workflow available",
  "Tavern workflow available",
  "World workflow available",
  "Cross-Mode proposals available",
  "Authoring / Mod available",
  "Quality Gate runnable",
  "Debug / Replay available",
  "Backup / Restore available",
  "Export / Diagnostics available",
  "Privacy boundaries pass"
]) {
  requireToken(backendWorkflow + desktopUi + app, label, `${label} workflow label`);
}

const uiBundle = `${app}\n${desktopUi}`;
if (desktopUi.includes("testProjectProviderConnection(")) {
  failures.push("Workflow checker UI should not run Provider connection tests directly.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(uiBundle)) {
  failures.push("Secret-looking sk-* token detected in workflow checker frontend source.");
}
if (/raw_provider_response|state_deltas\.map|state_deltas\.filter/i.test(desktopUi)) {
  failures.push("Workflow checker frontend includes raw debug/provider response wording outside exclusion copy.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i.test(uiBundle)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected.");
}

if (failures.length) {
  console.error("v3.7 workflow checker check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 workflow checker check passed.");
