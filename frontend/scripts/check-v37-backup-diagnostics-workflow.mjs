import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 32000);
}

requireToken(app, "function BackupRestoreDiagnosticsCompleteWorkflowChecklist", "Backup / Restore / Diagnostics Complete Workflow Check component");
requireToken(app, "data-v37-backup-diagnostics-workflow-check=\"safe-summary\"", "v3.7 Backup / Diagnostics workflow safe summary marker");
requireToken(app, "buildBackupRestoreDiagnosticsWorkflowChecklistItems", "Backup / Diagnostics workflow checklist builder");
requireToken(app, "Backup / Restore readiness", "Product dashboard Backup / Restore readiness item");
requireToken(app, "不做云备份", "cloud backup exclusion copy");
requireToken(app, "不上传", "upload exclusion copy");
requireToken(app, "不显示 secrets", "secret display exclusion copy");
requireToken(app, "默认不包含 mature/private/debug", "mature/private/debug default exclusion copy");
requireToken(app, "未确认时覆盖项目", "restore confirm boundary copy");
requireToken(app, "不修改 GameState", "GameState boundary copy");

for (const label of [
  "备份可用",
  "备份 dry-run 可用",
  "备份默认排除敏感内容",
  "恢复 dry-run 可用",
  "恢复 apply 需要确认",
  "诊断包预览可用",
  "诊断包导出可用",
  "诊断包默认排除敏感内容",
  "日志查看器会脱敏 secrets",
  "错误恢复可用",
  "安全路径摘要可用",
  "没有云备份",
  "不会上传"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const token of [
  "BackupRestoreWizardPanel",
  "备份 / 恢复向导",
  "备份 dry-run 预览",
  "确认创建本地备份",
  "恢复 dry-run 预览",
  "DiagnosticsBundlePanel",
  "诊断包预览",
  "DiagnosticsExportPanel",
  "诊断导出",
  "LocalLogViewerPanel",
  "本地日志查看器",
  "ErrorRecoveryWizardPanel",
  "错误恢复向导",
  "SafePathSummary",
  "LocalLongOperationProgress",
  "LOCAL_OPERATION_DEFAULT_EXCLUSIONS",
  "DIAGNOSTICS_EXCLUDED_SECTIONS"
]) {
  requireToken(app, token, `${token} backup/diagnostics integration`);
}

for (const token of [
  "备份 / 恢复",
  "备份 dry-run",
  "创建本地备份",
  "恢复 dry-run",
  "确认恢复",
  "诊断 / 日志",
  "预览诊断包",
  "创建本地诊断包",
  "Safe path summary",
  "Local project lifecycle checks do not upload data"
]) {
  requireToken(desktopUi, token, `${token} desktop/local lifecycle integration`);
}

requireToken(app, "backupPlan && backupPlan.local_only && backupPlan.dry_run", "backup dry-run safe status path");
requireToken(app, "backupSecretDefaultsSafe", "backup default secret exclusion status path");
requireToken(app, "restorePlan && restorePlan.local_only && restorePlan.dry_run", "restore dry-run safe status path");
requireToken(app, "恢复 apply 仍由后端确认并受显式确认门禁保护", "restore confirm required copy");
requireToken(app, "diagnosticsPreviewSafe", "diagnostics preview safe status path");
requireToken(app, "diagnosticsRedacted", "diagnostics redacted status path");
requireToken(app, "localLogsRedacted", "logs redacted status path");
requireToken(app, "recoveryReady", "error recovery ready status path");
requireToken(app, "containsSensitiveLogMarker", "log secret marker guard");
requireToken(app, "BACKUP_DEFAULT_EXCLUSION_TOKENS", "backup exclusion token list");
requireToken(app, "诊断包预览仅本地、仅预览，不写入文件", "diagnostics preview no write copy");
requireToken(app, "诊断包已在预览后本地创建；没有上传", "diagnostics no upload result copy");
for (const token of [
  "不包含 API key",
  "不包含 .env",
  "不包含 provider secrets",
  "不包含 debug raw data",
  "不包含 mature/private"
]) {
  requireToken(app, token, `Chinese filtering/exclusion summary ${token}`);
}

const checklist = sourceSlice(app, "function BackupRestoreDiagnosticsCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "handleBackupDryRun(",
  "handleCreateBackup(",
  "handleRestoreDryRun(",
  "createBackupDryRun(",
  "createLocalBackup(",
  "restoreBackupDryRun(",
  "restoreApply(",
  "previewDiagnosticsBundle(",
  "createDiagnosticsBundle(",
  "fetchLocalLogs(",
  "refreshRecovery(",
  "handleDryRunRecovery(",
  "fetch(",
  "setGameState(",
  "setVisibleState(",
  "submitPlayerInput(",
  "applyStateDelta"
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Backup / Diagnostics workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("Backup / Diagnostics workflow checklist includes API-key input or transient key terminology.");
}

if (/JSON\.stringify\([^)]*(env|prompt|state_delta|secret)/i.test(checklist) || /<pre>/i.test(checklist)) {
  failures.push("Backup / Diagnostics workflow checklist appears to render raw sensitive/debug payloads.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${desktopUi}`)) {
  failures.push("Secret-looking sk-* token detected in Backup / Diagnostics workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|CloudBackup|OnlineDiagnosticsUpload)/i.test(`${app}\n${desktopUi}`)) {
  failures.push("Online/account/cloud/marketplace/cloud-backup/diagnostics-upload enabling entrypoint detected.");
}

if (!pkg.scripts?.["check:v37-backup-diagnostics-workflow"]) {
  failures.push("package.json is missing check:v37-backup-diagnostics-workflow.");
}

if (failures.length) {
  console.error("v3.7 Backup / Restore / Diagnostics workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Backup / Restore / Diagnostics workflow check passed.");
