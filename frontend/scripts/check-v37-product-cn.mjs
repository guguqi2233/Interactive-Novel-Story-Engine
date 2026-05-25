import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const read = (...parts) => readFileSync(resolve(root, ...parts), "utf8");

const app = read("src", "App.tsx");
const providerUi = read("src", "providerUi.tsx");
const desktopUi = read("src", "desktopUi.tsx");
const pkg = JSON.parse(read("package.json"));
const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) failures.push(`Forbidden ${label}: ${token}`);
}

function forbidPattern(source, pattern, label) {
  if (pattern.test(source)) failures.push(`Forbidden ${label}: ${pattern}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 70000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const home = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const nav = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
const tour = sourceSlice(app, "function FirstRunOnboardingFlow", "function DiagnosticsExportPanel");
const providerWizard = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");
const combined = `${app}\n${providerUi}\n${desktopUi}`;

requireToken(app, "const CN_COPY", "Chinese copy layer");
requireToken(app, "function ChinesePlayableHomePanel", "Chinese playable home");
requireToken(app, "data-testid=\"v37-cn-playable-home\"", "Chinese Home test id");
requireToken(app + desktopUi, "本地 AI 叙事工作室", "Chinese product title");
requireToken(app + desktopUi, "中文本地可游玩完整产品", "Chinese playable product positioning");

for (const token of ["写小说", "角色 RP", "大世界游玩", "打开项目", "创建项目", "配置模型服务", "首次使用向导"]) {
  requireToken(home + app + desktopUi, token, `Chinese product copy ${token}`);
}

for (const token of ["无需账号", "不使用云同步", "无在线市场", "API Key 仅保存在本地", "不上传项目", "世界状态边界受保护"]) {
  requireToken(combined, token, `local-first Chinese notice ${token}`);
}

for (const token of [
  "testId=\"v38-open-novel-card\"",
  "testId=\"v38-open-tavern-card\"",
  "testId=\"v38-open-world-card\"",
  "data-testid=\"v38-provider-missing-cta\"",
  "data-testid=\"v37-project-entry-panel\"",
  "data-testid=\"v37-home-model-service-status\"",
  "data-testid=\"v37-mode-llm-status\"",
  "data-testid=\"v37-home-quality-status\"",
  "data-testid=\"v37-demo-project-entry\"",
  "examples/demo_local_narrative_project"
]) {
  requireToken(home + app, token, `Home product surface ${token}`);
}

for (const token of ["TimelineReplayPanel", "StateDeltaViewerPanel", "EventLogViewerPanel", "Product Readiness Dashboard", "raw_state_delta", "raw state_deltas", "<aside id=\"debug-panel\""]) {
  forbidToken(home, token, "default Home debug/developer surface");
}
if ((home.match(/\bdisabled=/g) ?? []).length > 0 || home.includes("<DisabledState")) {
  failures.push("Chinese playable Home should use contextual next steps instead of a disabled-button wall.");
}

for (const token of [
  "data-testid=\"v37-main-nav\"",
  "data-testid=\"v37-common-settings-nav\"",
  "data-testid=\"v37-advanced-tools-nav\"",
  "data-default-collapsed=\"true\"",
  "首页",
  "模型服务",
  "设置",
  "备份",
  "高级工具",
  "调试 / 回放"
]) {
  requireToken(nav + app, token, `Chinese reduced navigation ${token}`);
}
const advancedNavIndex = nav.indexOf("data-testid=\"v37-advanced-tools-nav\"");
const debugNavIndex = nav.indexOf("调试 / 回放");
if (advancedNavIndex < 0 || debugNavIndex < advancedNavIndex) {
  failures.push("Debug / Replay must be inside the Advanced Tools navigation.");
}

for (const token of [
  "data-testid=\"v38-first-run-tour-shell\"",
  "当前步骤",
  "查看全部步骤",
  "open={false}",
  "上一步",
  "下一步",
  "跳过",
  "完成"
]) {
  requireToken(tour + app, token, `Chinese first-run tour ${token}`);
}
for (const token of ["TimelineReplayPanel", "StateDeltaViewerPanel", "EventLogViewerPanel", "raw_state_delta"]) {
  forbidToken(tour, token, "first-run tour debug/developer token");
}

for (const token of [
  "模型服务设置向导",
  "OpenAI",
  "OpenAI-compatible",
  "中转站",
  "本地模型服务",
  "Base URL",
  "API Key",
  "手动添加 model_id",
  "模型分配",
  "不会在 UI 中显示"
]) {
  requireToken(providerWizard + providerUi, token, `Provider and Settings Chinese UI ${token}`);
}

for (const token of ["备份", "恢复", "诊断", "不会上传"]) {
  requireToken(desktopUi + app, token, `Backup / Diagnostics Chinese UI ${token}`);
}

forbidPattern(combined, /<input[^>]+name=["']api_key["']/i, "plaintext api_key input");
forbidPattern(combined, /localStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i, "API key persisted to localStorage");
forbidPattern(combined, /sessionStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i, "API key persisted to sessionStorage");
forbidPattern(combined, /Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{12,}/i, "Authorization bearer value");
forbidPattern(combined, /sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}/i, "real-looking API key");
forbidPattern(combined, /create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i, "onlineization entrypoint");

if (!pkg.scripts?.["check:v37-product-cn"]) {
  failures.push("package.json is missing check:v37-product-cn.");
}

if (failures.length) {
  console.error("v3.7 Chinese product UI check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Chinese product UI check passed.");
