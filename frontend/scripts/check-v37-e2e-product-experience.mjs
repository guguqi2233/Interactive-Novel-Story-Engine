import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidToken(source, token, label) {
  if (source.includes(token)) failures.push(`Forbidden ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 26000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const homeSlice = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const navSlice = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
const studioHomeSlice = sourceSlice(app, "function StudioHome", "function WorldHealthDashboard", 50000);

requireToken(app, "function ChinesePlayableHomePanel", "Chinese playable home component");
requireToken(app, "data-testid=\"v37-cn-playable-home\"", "Chinese product home test id");
requireToken(app, ") : mode === \"studio\" ? (\n            <DesktopStudioHome", "default studio route lazy-loads localized desktop home");
requireToken(desktopUi, "data-testid=\"v37-cn-playable-home\"", "default lazy desktop home renders Chinese playable home");
requireToken(desktopUi, "data-testid=\"v37-home-advanced-tools\"", "desktop dashboard folded into Advanced Tools");
forbidToken(desktopUi, "<h3>Local Desktop Studio</h3>", "old English developer dashboard heading on default desktop home");
requireToken(app, "本地 AI 叙事工作室", "Chinese product name");
requireToken(homeSlice, "写小说", "Novel main entry copy");
requireToken(homeSlice, "角色 RP", "Tavern main entry copy");
requireToken(homeSlice, "大世界游玩", "World main entry copy");
requireToken(homeSlice, "打开项目", "Open project CTA");
requireToken(homeSlice, "创建项目", "Create project CTA");
requireToken(homeSlice, "配置模型服务", "Provider setup CTA");
requireToken(homeSlice, "体验 Demo 项目", "Demo project CTA");
requireToken(homeSlice, "examples/demo_local_narrative_project", "Demo fixture path");
requireToken(homeSlice, "fake/local_stub provider", "Demo fake provider copy");
requireToken(homeSlice, "试写小说", "Demo Novel trial CTA");
requireToken(homeSlice, "试角色 RP", "Demo Tavern trial CTA");
requireToken(homeSlice, "试大世界游玩", "Demo World trial CTA");

for (const testId of [
  "cn-open-project",
  "cn-create-project",
  "cn-configure-provider",
  "cn-open-novel",
  "cn-open-tavern",
  "cn-open-world",
  "cn-continue-world",
  "cn-start-world",
  "v37-home-model-service-status",
  "v37-mode-llm-status",
  "v37-project-entry-panel",
  "v37-demo-project-entry"
]) {
  requireToken(homeSlice, `data-testid="${testId}"`, `Home user-path test id ${testId}`);
}

for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "Product Readiness Dashboard",
  "raw_state_delta",
  "raw state_deltas",
  "<pre>{JSON.stringify(event.state_deltas"
]) {
  forbidToken(homeSlice, token, "default Home debug/raw panel");
}

if ((homeSlice.match(/\bdisabled=/g) ?? []).length > 0 || homeSlice.includes("<DisabledState")) {
  failures.push("Home should show contextual next steps instead of a screen full of disabled controls.");
}

requireToken(studioHomeSlice, "data-testid=\"v37-home-advanced-tools\"", "Home advanced tools foldout");
requireToken(studioHomeSlice, "Quality Gate", "Quality advanced tool copy");
requireToken(studioHomeSlice, "Debug / Replay", "Debug advanced tool copy");
requireToken(studioHomeSlice, "Authoring / Mods", "Authoring advanced tool copy");
requireToken(studioHomeSlice, "Backup", "Backup entry copy");
requireToken(studioHomeSlice, "Diagnostics", "Diagnostics entry copy");
const advancedFoldIndex = studioHomeSlice.indexOf("data-testid=\"v37-home-advanced-tools\"");
const debugIndex = studioHomeSlice.indexOf("Debug / Replay");
if (advancedFoldIndex < 0 || debugIndex < advancedFoldIndex) {
  failures.push("Debug / Replay should be inside the Advanced Tools foldout on Home.");
}

requireToken(navSlice, "data-testid=\"v37-advanced-tools-nav\"", "Advanced Tools nav foldout");
requireToken(navSlice, "<span>Debug / Replay</span>", "Debug / Replay nav entry");
requireToken(navSlice, "cnLabel: CN_COPY.nav.novel", "Novel nav entry");
requireToken(navSlice, "cnLabel: CN_COPY.nav.tavern", "Tavern nav entry");
requireToken(navSlice, "cnLabel: CN_COPY.nav.world", "World nav entry");
requireToken(navSlice, "cnLabel: CN_COPY.nav.provider", "Provider nav entry");
const advancedNavIndex = navSlice.indexOf("data-testid=\"v37-advanced-tools-nav\"");
const debugNavIndex = navSlice.indexOf("<span>Debug / Replay</span>");
if (advancedNavIndex < 0 || debugNavIndex < advancedNavIndex) {
  failures.push("Debug / Replay must be grouped under Advanced Tools in navigation.");
}

requireToken(providerUi, "模型服务设置向导", "Provider setup wizard Chinese copy");
requireToken(providerUi, "测试连接", "manual test connection copy");
requireToken(providerUi, "读取模型", "fetch models copy");
requireToken(providerUi, "手动添加 model_id", "manual model id copy");
requireToken(providerUi, "小说草稿", "Novel assignment use case copy");
requireToken(providerUi, "Tavern 回复", "Tavern assignment use case copy");
requireToken(providerUi, "世界输入解析", "World intent assignment copy");
requireToken(providerUi, "世界叙事渲染", "World narration assignment copy");
requireToken(providerUi, "allow_real_connection: allowRealProviderCall", "manual connection opt-in flag");
requireToken(providerUi, "allow_real_provider: allowRealProviderCall", "manual model fetch opt-in flag");
requireToken(api, "fetchProjectProviderModels", "fetch models frontend API");
requireToken(api, "syncProjectProviderModels", "sync models frontend API");
requireToken(api, "saveProjectProviderModelAssignments", "model assignment frontend API");

requireToken(desktopUi, "备份", "Backup Chinese entry");
requireToken(desktopUi, "诊断", "Diagnostics Chinese entry");
requireToken(desktopUi, "不会上传", "no upload diagnostics/backup copy");

for (const token of ["无需账号", "不使用云同步", "无在线市场"]) {
  requireToken(app, token, `local-only notice ${token}`);
}

const safeSurface = `${homeSlice}\n${navSlice}\n${providerUi}\n${desktopUi}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(safeSurface)) {
  failures.push("Secret-looking sk-* token detected in product experience UI.");
}
if (/Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{8,}/i.test(safeSurface)) {
  failures.push("Authorization bearer value detected in product experience UI.");
}
if (/localStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i.test(safeSurface)) {
  failures.push("Product experience UI must not persist API keys or transient keys to localStorage.");
}
if (/sessionStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i.test(safeSurface)) {
  failures.push("Product experience UI must not persist API keys or transient keys to sessionStorage.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemotePackageDownload)/i.test(safeSurface)) {
  failures.push("Account/cloud/marketplace/remote download entrypoint detected in v3.7 product experience UI.");
}

if (!pkg.scripts?.["check:v37-e2e-product-experience"]) {
  failures.push("package.json is missing check:v37-e2e-product-experience.");
}

if (failures.length) {
  console.error("v3.7 E2E product experience check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 E2E product experience check passed.");
