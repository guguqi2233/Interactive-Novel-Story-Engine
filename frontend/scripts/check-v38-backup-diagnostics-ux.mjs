import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}`);
  }
}

function requireAbsent(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}`);
  }
}

function sliceFunction(name, nextName) {
  const start = app.indexOf(`function ${name}`);
  const end = nextName ? app.indexOf(`function ${nextName}`, start) : -1;
  if (start < 0) {
    failures.push(`Missing function ${name}`);
    return "";
  }
  return app.slice(start, end > start ? end : undefined);
}

const diagnostics = sliceFunction("DiagnosticsBundlePanel", "normalizeDiagnosticsSections");
const backup = sliceFunction("BackupRestoreWizardPanel", "ErrorRecoveryWizardPanel");
const combined = `${diagnostics}\n${backup}`;

requireToken(diagnostics, "data-testid=\"v38-diagnostics-filtering-summary\"", "diagnostics filtering summary");
requireToken(backup, "data-testid=\"v38-backup-restore-filtering-summary\"", "backup/restore filtering summary");

for (const token of [
  "诊断包预览",
  "备份 / 恢复向导",
  "备份 dry-run 预览",
  "恢复 dry-run 预览",
  "确认创建本地备份",
  "恢复必须确认",
  "先 dry-run，再 confirm",
  "不会自动覆盖项目",
  "中文确认门禁",
  "不会上传",
  "仅本地",
  "API Key",
  ".env",
  "Provider secrets",
  "debug raw data",
  "mature/private",
  "raw state_deltas",
  "中文安全错误",
  "脱敏错误摘要"
]) {
  requireToken(combined, token, `backup/diagnostics UX copy: ${token}`);
}

for (const token of [
  "fetch(\"http",
  "XMLHttpRequest",
  "navigator.sendBeacon",
  "uploadDiagnostics",
  "cloud backup",
  "Authorization:",
  "Bearer ",
  "transient_api_key",
  "localStorage.setItem(\"api",
  "sessionStorage.setItem(\"api"
]) {
  requireAbsent(combined, token, `backup/diagnostics forbidden token: ${token}`);
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(combined)) {
  failures.push("Backup/diagnostics slice appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-backup-diagnostics-ux"] ?? "", "node scripts/check-v38-backup-diagnostics-ux.mjs", "package script");

if (failures.length) {
  console.error("v3.8 backup/diagnostics UX check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 backup/diagnostics UX check passed.");
