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

const requiredAuthoringTokens = [
  "AuthoringWorkspaceShell",
  "WorldPackWizardPanel",
  "Script Package Builder",
  "Character Pack",
  "Quest Graph",
  "Location Cluster Templates",
  "NPC Goal Editor",
  "Faction and NPC relationship authoring",
  "ActionModEditorPanel",
  "ActionModTestHarnessPanel",
  "Rule Module",
  "RuleModuleContractPanel",
  "ModuleBrowserProPanel",
  "ModPermissionDashboardProPanel",
  "CompatibilityMatrixProPanel",
  "ExtensionCertificationProPanel",
  "ImportExportWizardProPanel",
  "ModQualityGateProPanel",
  "AuthoringValidationDashboardPanel",
  "AuthoringDiffPreview",
  "AuthoringOnlyPreviewDetails",
  "redactAuthoringPreviewText",
  "redactReportText",
  "AuthoringAuditTrailPanel",
  "AuthoringBackupRestorePanel",
  "SafeApplyWorkflowPanel"
];

const requiredSafetyCopy = [
  "local-only",
  "No online marketplace",
  "No remote download",
  "No arbitrary code execution",
  "API keys",
  "provider secrets",
  "hidden facts",
  "raw state_deltas",
  "does not modify active GameState"
];

const failures = [];

for (const token of requiredAuthoringTokens) {
  if (!source.includes(token)) failures.push(`Missing Authoring / Mod UI Pro token: ${token}`);
}

for (const token of requiredSafetyCopy) {
  if (!source.includes(token)) failures.push(`Missing Authoring safety/local-first copy: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(source) || /api_key:\s*["'][^"']+/i.test(source)) {
  failures.push("Plaintext api_key input or literal detected in frontend source.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(source + scripts)) {
  failures.push("Secret-looking sk-* token detected in frontend files.");
}

if (/JSON\.stringify\(event\.state_deltas/i.test(source) && !source.includes("DebugGate")) {
  failures.push("Raw state_deltas JSON rendering detected in normal frontend source.");
}

if (/<pre>\{previewContent\}<\/pre>/.test(source)) {
  failures.push("Authoring preview content renders raw previewContent instead of redacted safe preview.");
}

if (/issue\.message/.test(source) && !/redactReportText\(issue\.message\)/.test(source)) {
  failures.push("Authoring validation issue messages are not consistently redacted.");
}

if (/moduleQualityGate\.blockers[\s\S]{0,180}<span key=\{item\}>\{item\}<\/span>/.test(source)) {
  failures.push("Module quality gate blockers render raw issue text.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Marketplace|Remote Download)\s*<\/h[1-6]>/i,
  /enable dangerous permission/i,
  /override dangerous permission/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(source)) failures.push("Online/remote/dangerous permission UI appears as a primary or enabling surface.");
}

if (!/"check:v34-authoring-ui"/.test(pkg)) failures.push("package.json is missing check:v34-authoring-ui.");

if (failures.length) {
  console.error("v3.4 Authoring UI regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.4 Authoring UI regression check passed.");
