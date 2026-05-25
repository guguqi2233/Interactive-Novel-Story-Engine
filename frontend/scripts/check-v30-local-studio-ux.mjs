import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src/App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src/api.ts"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");

const requiredAppTokens = [
  ["Local Launcher / Startup Status"],
  ["Project Selector"],
  ["Recent Projects"],
  ["Local Config Wizard"],
  ["Provider Setup Wizard"],
  ["Desktop Health Check"],
  ["One-Click Quality Gate"],
  ["Backup / Restore Wizard", "备份 / 恢复"],
  ["Error Recovery Wizard"],
  ["Local Log Viewer", "本地日志查看器"],
  ["Diagnostics Bundle UI", "诊断 / 日志"],
  ["Offline Help Center", "离线帮助中心"],
  ["Settings / Preferences Sections", "产品设置分区"],
  ["First-Run Onboarding", "首次使用向导"],
  ["SafePathSummary"],
  ["No account needed", "无需账号"],
  ["No cloud sync", "不使用云同步"],
  ["No online marketplace", "无在线市场"],
  ["API keys stay local", "API Key 仅保存在本地"],
  ["Nothing is uploaded", "不会上传", "不上传项目"],
  ["Mature Module default off", "Mature 默认关闭", "Mature Module is disabled by default."]
];

const requiredCompletionTokens = [
  ["Retry Health Check"],
  ["Open Local Config Wizard"],
  ["View Local Logs"],
  ["SQLite / Database"],
  ["Workspace"],
  ["Logs"],
  ["Workspace root"],
  ["Log directory"],
  ["Backup directory"],
  ["Privacy defaults"],
  ["safe provider status"],
  ["Explicit Confirm Create Backup", "确认在 dry-run 之后创建本地备份", "写入必须显式确认"],
  ["Restore Dry-Run Preview", "恢复 dry-run 预览", "Restore dry-run preview"],
  ["Restart backend/frontend", "Restart backend", "重启"],
  ["Reload project summary", "刷新设置", "刷新"],
  ["Level filter", "level", "级别"],
  ["Component filter", "Component", "组件"],
  ["Last run summary"],
  ["Project id"],
  ["Mode status"],
  ["Pin"],
  ["Desktop Packaging"]
];

const requiredApiTokens = [
  "fetchLocalStudioStatus",
  "fetchLocalStudioConfigSummary",
  "fetchLocalStudioStartupChecks",
  "createBackupDryRun",
  "restoreBackupDryRun",
  "fetchRecoveryIssues",
  "fetchLocalLogs",
  "previewDiagnosticsBundle"
];

const failures = [];

for (const alternatives of requiredAppTokens) {
  if (!alternatives.some((token) => app.includes(token))) failures.push(`Missing v3.0 UX token: ${alternatives.join(" | ")}`);
}

for (const alternatives of requiredCompletionTokens) {
  if (!alternatives.some((token) => app.includes(token))) failures.push(`Missing v3.0 completion token: ${alternatives.join(" | ")}`);
}

for (const token of requiredApiTokens) {
  if (!api.includes(token)) failures.push(`Missing v3.0 API helper: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(app) || /api_key:\s*["'][^"']+/i.test(app)) {
  failures.push("Plaintext api_key input or literal detected.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(app + api)) {
  failures.push("Secret-looking sk-* token detected in frontend source.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(app)) failures.push("Account/cloud/marketplace appears as a primary UI entry.");
}

if (!/"check:v30-ux"/.test(pkg)) failures.push("package.json is missing check:v30-ux.");

if (failures.length) {
  console.error("v3.0 Local Studio UX safety check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.0 Local Studio UX safety check passed.");
