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

requireToken(app, "function ExportCompleteWorkflowChecklist", "Export Complete Workflow Check component");
requireToken(app, "data-v37-export-workflow-check=\"safe-summary\"", "v3.7 Export workflow safe summary marker");
requireToken(app, "buildExportWorkflowChecklistItems", "Export workflow checklist builder");
requireToken(app, "Export Complete Workflow Check", "Export workflow dashboard title");
requireToken(app, "Local export readiness across Novel, Tavern, World archive, Authoring / Mod packages, Diagnostics", "cross-surface export readiness copy");
requireToken(app, "no online publishing", "online publishing exclusion copy");
requireToken(app, "no cloud sync", "cloud sync exclusion copy");
requireToken(app, "no upload", "upload exclusion copy");
requireToken(app, "no default debug export", "debug default exclusion copy");
requireToken(app, "no mature/private export by default", "mature/private default exclusion copy");
requireToken(app, "no secret export", "secret export exclusion copy");
requireToken(app, "no real provider call", "provider call exclusion copy");

for (const label of [
  "Novel export available",
  "Tavern export available",
  "Mod/package export available",
  "Diagnostics export available",
  "export preview available",
  "filtering summary visible",
  "secrets excluded",
  "hidden refs excluded",
  "mature/private excluded by default",
  "debug excluded by default",
  "export confirm required",
  "no upload"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const token of [
  "NovelExportWizard",
  "exportNovelManuscript",
  "previewTavernSessionExport",
  "createTavernSessionExport",
  "exportWorldArchive",
  "exportScriptPackage",
  "exportNPCPackGenerator",
  "DiagnosticsBundlePanel",
  "DiagnosticsExportPanel",
  "SafeDebugExportWizard",
  "confirmDangerousAction",
  "Default filtering excludes",
  "Tavern export preview generated. No file was written.",
  "Nothing was uploaded.",
  "Safe character pack export preview is ready.",
  "Import is dry-run first; export previews safe manifests"
]) {
  requireToken(app, token, `${token} export integration`);
}

requireToken(app, "diagnosticsPreviewSafe", "diagnostics export preview safety status");
requireToken(app, "diagnosticsBundlePreview.local_only", "diagnostics local-only preview guard");
requireToken(app, "!diagnosticsBundlePreview.writes_file", "diagnostics preview no-write guard");
requireToken(app, "!diagnosticsBundlePreview.manifest.contains_secrets", "diagnostics no-secret guard");
requireToken(app, "!diagnosticsBundlePreview.manifest.contains_hidden_debug_mature_private", "diagnostics hidden/debug/mature guard");
requireToken(app, "exportFilteringSafe", "export filtering safety status");
requireToken(app, "Safe Debug Export requires ENABLE_DEBUG_API and explicit confirmation", "debug export gated copy");
requireToken(app, "the readiness checklist never creates files", "read-only checklist copy");

const checklist = sourceSlice(app, "function ExportCompleteWorkflowChecklist", "function LocalPrivacySafetyCompleteReviewPanel");
for (const forbidden of [
  "handleExport(",
  "handlePreviewTavernExport(",
  "handleCreateTavernExport(",
  "handleCharacterPackExport(",
  "handleExportScriptPackage(",
  "handleCreateDiagnosticsBundle(",
  "exportNovelManuscript(",
  "previewTavernSessionExport(",
  "createTavernSessionExport(",
  "exportWorldArchive(",
  "exportScriptPackage(",
  "exportNPCPackGenerator(",
  "createDiagnosticsBundle(",
  "previewDiagnosticsBundle(",
  "fetch(",
  "setGameState(",
  "setVisibleState(",
  "submitPlayerInput(",
  "applyStateDelta"
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Export workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("Export workflow checklist includes API-key input or transient key field.");
}

if (/JSON\.stringify\([^)]*(env|prompt|state_delta|secret|hidden)/i.test(checklist) || /<pre>/i.test(checklist)) {
  failures.push("Export workflow checklist appears to render raw sensitive/debug payloads.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(app)) {
  failures.push("Secret-looking sk-* token detected in Export workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|OnlinePublish|OnlineExport|UploadExport)/i.test(app)) {
  failures.push("Online/account/cloud/marketplace/upload export enabling entrypoint detected.");
}

if (!pkg.scripts?.["check:v37-export-workflow"]) {
  failures.push("package.json is missing check:v37-export-workflow.");
}

if (failures.length) {
  console.error("v3.7 Export workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Export workflow check passed.");
