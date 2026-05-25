import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 30000);
}

requireToken(app, "function AuthoringModCompleteWorkflowChecklist", "Authoring / Mod Complete Workflow Check component");
requireToken(app, "data-v37-authoring-mod-workflow-check=\"safe-summary\"", "v3.7 Authoring / Mod workflow safe summary marker");
requireToken(app, "buildAuthoringModWorkflowChecklistItems", "Authoring / Mod workflow checklist builder");
requireToken(app, "Authoring / Mod readiness", "Product dashboard Authoring / Mod readiness item");
requireToken(app, "no package execution", "package execution exclusion copy");
requireToken(app, "no upload", "upload exclusion copy");
requireToken(app, "no online marketplace", "online marketplace exclusion copy");
requireToken(app, "no remote download", "remote download exclusion copy");
requireToken(app, "no automatic apply", "automatic apply exclusion copy");
requireToken(app, "no active GameState mutation", "active GameState mutation exclusion copy");
requireToken(app, "Safe Apply still requires validation, dry-run, explicit confirm, and audit", "Safe Apply gate copy");

for (const label of [
  "World Pack Editor available",
  "Script Pack Editor available",
  "Character Pack Editor available",
  "Quest/Location/NPC/Item/Rumor editors available",
  "Action Mod Editor available",
  "Rule Module Contract UI available",
  "Module Browser available",
  "Permission Dashboard available",
  "Compatibility Matrix available",
  "Certification available",
  "Import/Export Wizard available",
  "Mod Quality Gate available",
  "Validation Dashboard available",
  "Diff/Preview/Dry-Run available",
  "Safe Apply available",
  "Authoring audit trail available",
  "no arbitrary code execution",
  "no direct active GameState mutation"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const token of [
  "AuthoringStudioProDashboard",
  "World Pack Editor Pro",
  "Script Pack Editor Pro",
  "Character Pack Editor Pro",
  "Quest Graph Editor Pro",
  "Location / Map Authoring Pro",
  "NPC / Faction / Relationship Authoring Pro",
  "Item / Economy / Trade Authoring Pro",
  "Rumor / Crime / Consequence Authoring Pro",
  "ActionModEditorPanel",
  "RuleModuleContractPanel",
  "ModuleBrowserProPanel",
  "ModPermissionDashboardProPanel",
  "CompatibilityMatrixProPanel",
  "ExtensionCertificationProPanel",
  "ImportExportWizardProPanel",
  "ModQualityGateProPanel",
  "AuthoringValidationDashboardPanel",
  "AuthoringDiffPreview",
  "AuthoringAuditTrailPanel",
  "SafeApplyWorkflowPanel"
]) {
  requireToken(app, token, `${token} Authoring / Mod integration`);
}

requireToken(app, "No online marketplace", "Authoring shell no online marketplace status");
requireToken(app, "No remote download", "Authoring shell no remote download status");
requireToken(app, "No arbitrary code execution", "Authoring shell no arbitrary code execution status");
requireToken(app, "Authoring does not modify active GameState", "Authoring active GameState boundary copy");
requireToken(app, "Safe apply writes local content/project files only after validation, dry-run, and explicit confirm. It does not modify active GameState", "Safe Apply boundary copy");
requireToken(app, "Dangerous permissions are default-deny", "dangerous permission blocked copy");
requireToken(app, "without running module code", "Rule Module contract-only copy");
requireToken(app, "Provider Profile Pack export may contain api_key_env or secret_ref only, never a raw key", "Provider profile export secret boundary copy");

const checklist = sourceSlice(app, "function AuthoringModCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "saveAuthoringFile(",
  "saveAuthoringMap(",
  "saveQuestGraph(",
  "saveNPCGoalGraph(",
  "saveItemEconomyAuthoring(",
  "saveRumorCrimeAuthoring(",
  "buildScriptPackage(",
  "exportScriptPackage(",
  "importPackage(",
  "handleImport(",
  "runModuleCertification(",
  "runModQualityGate(",
  "applyStateDelta",
  "submitPlayerInput(",
  "setVisibleState(",
  "setGameState(",
  "fetch(",
  "eval(",
  "new Function"
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Authoring / Mod workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist)) {
  failures.push("Authoring / Mod workflow checklist includes an API-key input.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(app)) {
  failures.push("Secret-looking sk-* token detected in Authoring / Mod workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|OnlinePackageRegistry)/i.test(app)) {
  failures.push("Online/account/cloud/marketplace/remote-download enabling entrypoint detected in Authoring / Mod workflow source.");
}

if (!pkg.scripts?.["check:v37-authoring-mod-workflow"]) {
  failures.push("package.json is missing check:v37-authoring-mod-workflow.");
}

if (failures.length) {
  console.error("v3.7 Authoring / Mod workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Authoring / Mod workflow check passed.");
