import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const read = (...parts) => readFileSync(resolve(root, ...parts), "utf8");

const app = read("src", "App.tsx");
const api = read("src", "api.ts");
const providerUi = read("src", "providerUi.tsx");
const desktopUi = read("src", "desktopUi.tsx");
const packageJson = JSON.parse(read("package.json"));
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

function sourceSlice(source, startToken, endToken, fallbackLength = 80000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

function requireDebugGate(source, usageToken, label) {
  const usage = source.indexOf(usageToken);
  const gateOpen = source.lastIndexOf("<DebugGate", usage);
  const gateClose = source.lastIndexOf("</DebugGate>", usage);
  if (usage < 0) {
    failures.push(`Missing ${label}: ${usageToken}`);
  } else if (gateOpen < 0 || gateOpen < gateClose) {
    failures.push(`${label} is not inside an active DebugGate region.`);
  }
}

const home = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const nav = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
const providerWizard = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");
const worldPanel = sourceSlice(app, "function WorldStudioPanel", "function CrossModeBridgePanel");
const advancedHome = sourceSlice(app, "data-testid=\"v37-home-advanced-tools\"", "function ProductHomeRedesignPanel", 30000);
const backendUnavailable = sourceSlice(app, "function BackendUnavailableState", "function ProviderMissingState");

// Route and mode surfaces should still load after v3.8 UX polish.
for (const [token, label] of [
  ["function ChinesePlayableHomePanel", "Home route/component"],
  ["lazyNamed(() => import(\"./providerUi\")", "Provider route lazy import"],
  ["lazyNamed(() => import(\"./novelUi\")", "Novel route lazy import"],
  ["lazyNamed(() => import(\"./tavernUi\")", "Tavern route lazy import"],
  ["lazyNamed(() => import(\"./worldUi\")", "World route lazy import"],
  ["<Suspense", "route Suspense fallback"],
  ["<AppErrorBoundary", "route ErrorBoundary"],
  ["data-testid=\"v37-cn-playable-home\"", "Chinese playable Home root"],
  ["cn-open-novel", "Novel entry action"],
  ["cn-open-tavern", "Tavern entry action"],
  ["cn-open-world", "World entry action"],
  ["data-testid=\"v37-advanced-tools-nav\"", "Advanced tools nav"],
  ["data-testid=\"v37-home-advanced-tools\"", "Advanced tools Home section"]
]) {
  requireToken(app, token, label);
}

// Home remains product-facing and does not default to debug/developer panels.
for (const token of ["写小说", "角色 RP", "大世界游玩", "配置模型服务"]) {
  requireToken(home + app, token, `Chinese Home/product copy ${token}`);
}
for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "Product Readiness Dashboard",
  "<aside id=\"debug-panel\"",
  "<pre>{JSON.stringify(event.state_deltas",
  "raw_state_deltas"
]) {
  forbidToken(home, token, "default Home debug/developer surface");
}
if ((home.match(/\bdisabled=/g) ?? []).length > 0 || home.includes("<DisabledState")) {
  failures.push("Home should not regress into a disabled-button wall.");
}

// Advanced tools are findable but folded away from the default play flow.
requireToken(app, "data-default-collapsed=\"true\"", "advanced tools default collapsed marker");
for (const token of ["Cross-Mode", "创作 / Mod", "质量检查", "调试 / 回放", "诊断", "导出"]) {
  requireToken(nav + advancedHome + app, token, `Advanced tool label ${token}`);
}
const advancedIndex = nav.indexOf("data-testid=\"v37-advanced-tools-nav\"");
const debugIndex = nav.indexOf("调试 / 回放");
if (advancedIndex < 0 || debugIndex < advancedIndex) {
  failures.push("Debug / Replay should stay grouped under Advanced Tools.");
}

// Backend unavailable and provider missing states stay safe and actionable.
for (const token of ["本地后端未连接", "重新连接", "查看启动指南", "打开诊断", "打开设置"]) {
  requireToken(backendUnavailable + app, token, `Backend unavailable recovery copy ${token}`);
}
for (const token of ["data-testid=\"v38-provider-missing-cta\"", "配置模型服务", "Provider", "Base URL", "API Key"]) {
  requireToken(app + providerWizard, token, `Provider missing/setup token ${token}`);
}

// Provider runtime and model assignment surfaces remain wired without rendering secrets.
for (const token of [
  "fetchProjectProviderModels",
  "syncProjectProviderModels",
  "saveProjectProviderModelAssignments",
  "allow_real_connection: allowRealProviderCall",
  "allow_real_provider: allowRealProviderCall",
  "local_stub",
  "mock",
  "手动添加 model_id",
  "世界输入解析",
  "JSON"
]) {
  requireToken(api + providerUi + app, token, `Provider/model assignment token ${token}`);
}

// World play still routes through backend game APIs instead of direct GameState mutation.
for (const token of ["submitPlayerInput", "\"/game/input\"", "startGame", "\"/game/start\""]) {
  requireToken(api + app + worldPanel, token, `World backend action API token ${token}`);
}
forbidPattern(worldPanel, /setGameState\s*\(/, "direct GameState setter in World UI");
forbidPattern(app, /applyStateDelta\s*\(/, "direct StateDelta apply in frontend");

// Debug-sensitive panels remain gated.
requireDebugGate(app, "<StateDeltaViewerPanel", "StateDelta Viewer");
requireDebugGate(app, "<VisibleDebugStateCompare", "Visible vs Debug Compare");
requireToken(app, "ENABLE_DEBUG_API", "Debug disabled explanation");

// Normal UI and safe product surfaces do not render secrets or hidden/raw debug data.
const renderedSafeSurface = [home, nav, providerWizard, desktopUi].join("\n");
forbidPattern(renderedSafeSurface, /sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}/i, "real-looking API key");
forbidPattern(renderedSafeSurface, /Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]+/i, "Authorization bearer value");
forbidPattern(renderedSafeSurface, /<input[^>]+name=["']api_key["']/i, "plaintext api_key input");
forbidToken(renderedSafeSurface, "hidden_fact_text", "hidden fact text in normal UI");
forbidToken(renderedSafeSurface, "npc_secret", "NPC secret token in normal UI");
forbidToken(home, "state_deltas.map", "raw state_delta mapping on Home");

// Local-first notices remain present without adding account/cloud/marketplace entry points.
for (const token of ["无需账号", "不使用云同步", "无在线市场", "不上传项目"]) {
  requireToken(app + desktopUi, token, `local-first Chinese notice ${token}`);
}
forbidPattern(app + providerUi + desktopUi, /create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i, "onlineization entrypoint");
forbidPattern(app + providerUi + desktopUi, /<button[^>]*>\s*(账号|云同步|在线市场|远程下载)\s*<\/button>/i, "onlineization button");

if (!packageJson.scripts?.["check:v38-integration-regression"]) {
  failures.push("package.json is missing check:v38-integration-regression.");
}

if (failures.length) {
  console.error("v3.8 integration regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 integration regression check passed.");
