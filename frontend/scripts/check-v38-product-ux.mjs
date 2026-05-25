import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) failures.push(`Forbidden ${label}: ${token}`);
}

function requireRegex(source, pattern, label) {
  if (!pattern.test(source)) failures.push(`Missing ${label}: ${pattern}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 60000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const home = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const nav = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
const tour = sourceSlice(app, "function FirstRunOnboardingFlow", "function DiagnosticsExportPanel");
const diagnostics = sourceSlice(app, "function DiagnosticsBundlePanel", "function BackupRestoreWizardPanel");
const backup = sourceSlice(app, "function BackupRestoreWizardPanel", "function ErrorRecoveryWizardPanel");
const providerWizard = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");

// 1. Home Chinese product identity and main mode entries.
requireToken(app, "本地 AI 叙事工作室", "Chinese product title");
requireToken(home, "data-testid=\"v37-cn-playable-home\"", "Home root");
requireToken(home, "写小说", "Novel entry");
requireToken(home, "角色 RP", "Tavern entry");
requireToken(home, "大世界游玩", "World entry");
requireToken(home, "testId=\"v38-open-novel-card\"", "Novel main card");
requireToken(home, "testId=\"v38-open-tavern-card\"", "Tavern main card");
requireToken(home, "testId=\"v38-open-world-card\"", "World main card");

// 2. Home must not regress into a default developer/debug console.
for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "<aside id=\"debug-panel\"",
  "<pre>{JSON.stringify(event.state_deltas",
  "raw_state_deltas",
  "Product Readiness Dashboard"
]) {
  forbidToken(home, token, "default Home debug/developer surface");
}
if ((home.match(/\bdisabled=/g) ?? []).length > 0 || home.includes("<DisabledState")) {
  failures.push("Home should use contextual next steps instead of a disabled-button wall.");
}

// 3. Advanced tools stay collapsed and findable.
requireToken(app, "data-testid=\"v37-home-advanced-tools\"", "advanced tools section");
requireToken(app, "data-default-collapsed=\"true\"", "advanced tools default collapsed marker");
requireToken(app, "高级工具", "Advanced tools Chinese label");
requireToken(app, "调试 / 回放", "Debug/Replay Chinese label");

// 4. Provider and backend recovery guidance.
requireToken(app, "data-testid=\"v38-provider-missing-cta\"", "Provider missing CTA");
requireToken(app, "配置模型服务", "Provider setup CTA");
requireToken(app, "data-testid=\"v38-backend-unavailable-state\"", "Backend unavailable recovery");
requireToken(app, "本地后端未连接", "Backend unavailable Chinese text");
requireToken(app, "重新连接", "Reconnect action");
requireToken(app, "查看启动指南", "Startup guide action");
requireToken(providerWizard, "模型服务设置向导", "Provider wizard Chinese title");
requireToken(providerWizard, "什么是 Base URL", "Provider Base URL explanation");
requireToken(providerWizard, "什么是 API Key", "Provider API Key explanation");

// 5. First-run tour is a product guide, not a full checklist wall.
requireToken(tour, "data-testid=\"v38-first-run-tour-shell\"", "simplified tour shell");
requireToken(tour, "当前步骤", "current tour step");
requireToken(app, "查看全部步骤", "collapsible all steps label");
requireToken(tour, "open={false}", "all steps default collapsed");
requireToken(app, "跳过", "skip action");
requireToken(app, "完成", "finish action");
for (const token of ["TimelineReplayPanel", "StateDeltaViewerPanel", "Product Readiness Dashboard"]) {
  forbidToken(tour, token, "tour debug/checklist surface");
}

// 6. Settings / Backup / Diagnostics Chinese product states.
requireToken(app, "设置", "Settings Chinese state");
requireToken(app, "常规、隐私、Provider、导出、Debug、备份、诊断、Mature 和 UI 偏好", "Settings section summary");
requireToken(backup, "备份 / 恢复向导", "Backup/restore Chinese title");
requireToken(backup, "备份不会上传", "Backup no upload wording");
requireToken(diagnostics, "诊断包预览", "Diagnostics Chinese title");
requireToken(diagnostics, "不会上传", "Diagnostics no upload wording");

// 7. Local-first / no-onlineization copy remains visible but does not dominate Home.
for (const token of ["无需账号", "不使用云同步", "无在线市场", "不上传项目"]) {
  requireToken(app, token, `local-first Chinese copy ${token}`);
}

// 8. Secret and raw debug safety.
requireRegex(app + providerUi, /API Key (?:不|仅|只)/, "API Key safety Chinese copy");
if (/sk-[A-Za-z0-9_-]{12,}/.test(app + providerUi)) {
  failures.push("Found secret-looking sk-* token in frontend source.");
}
for (const token of ["Authorization header", "raw env", "raw provider error"]) {
  requireToken(app + providerUi, token, `redaction copy ${token}`);
}

requireToken(styles, ".home-advanced-tools", "advanced tools styles");
requireToken(styles, ".cn-mode-entry-featured", "main mode card style");
if (!pkg.scripts?.["check:v38-product-ux"]) {
  failures.push("package.json is missing check:v38-product-ux.");
}

if (failures.length) {
  console.error("v3.8 product UX regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 product UX regression check passed.");
