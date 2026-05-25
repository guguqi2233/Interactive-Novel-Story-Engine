import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
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

function sourceSlice(source, startToken, endToken, fallbackLength = 22000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

function countMatches(source, pattern) {
  return Array.from(source.matchAll(pattern)).length;
}

function requireTokens(source, tokens, label) {
  for (const token of tokens) requireToken(source, token, `${label} ${token}`);
}

requireToken(app, "const CN_COPY", "lightweight Chinese copy layer");
requireToken(app, "function ChinesePlayableHomePanel", "Chinese playable home component");
requireToken(app, "data-testid=\"v37-cn-playable-home\"", "Chinese playable home test id");
requireToken(app, ") : mode === \"studio\" ? (\n            <DesktopStudioHome", "default studio route lazy-loads localized desktop home");
requireToken(desktopUi, "data-testid=\"v37-cn-playable-home\"", "default lazy desktop home renders Chinese playable home");
requireToken(desktopUi, "data-testid=\"v37-home-advanced-tools\"", "desktop dashboard folded into Advanced Tools");
forbidToken(desktopUi, "<h3>Local Desktop Studio</h3>", "old English developer dashboard heading on default desktop home");
requireToken(app, "function UnifiedNavigation", "reduced navigation component");
requireToken(app, "function FirstRunOnboardingFlow", "Chinese first-run tour component");
requireToken(app, "const PLAYABLE_PRODUCT_TOUR_STEPS", "playable product tour steps");
requireToken(app, "className={`app-shell ${debugOpen ? \"with-debug\" : \"without-debug\"}`}", "debug-free default shell layout");
requireToken(app, "useState<boolean>(false)", "Debug / Replay drawer hidden by default");
requireToken(app, "{debugOpen && (\n      <aside id=\"debug-panel\"", "Debug / Replay panel renders only after explicit open");
requireToken(app, "const mainEntryIds = hasProject ? [\"project\", \"novel\", \"tavern\", \"world\"] : [\"project\", \"provider\"];", "no-project navigation reduced to project/provider");
requireToken(app, "const commonSettingIds = hasProject ? [\"provider\", \"settings\", \"backup\"] : [];", "no-project common settings hidden");
requireToken(app, "const advancedToolIds = [\"cross-mode\", \"authoring\", \"qa\", \"diagnostics\", \"export\"];", "advanced developer tools grouped");

requireTokens(app, [
  "本地 AI 叙事工作室",
  "中文本地可游玩完整产品",
  "写小说",
  "角色 RP",
  "大世界游玩",
  "打开项目",
  "创建项目",
  "配置模型服务",
  "首次使用向导",
  "高级工具",
  "无需账号",
  "不使用云同步",
  "无在线市场",
  "API Key 仅保存在本地",
  "不上传项目",
  "世界状态边界受保护"
], "core Chinese product copy");

const homeSlice = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
requireTokens(homeSlice, [
  "data-testid=\"cn-open-project\"",
  "data-testid=\"cn-create-project\"",
  "data-testid=\"cn-configure-provider\"",
  "data-testid=\"cn-open-novel\"",
  "data-testid=\"cn-open-tavern\"",
  "data-testid=\"cn-open-world\"",
  "data-testid=\"v37-project-entry-panel\"",
  "data-testid=\"v37-home-model-service-status\"",
  "data-testid=\"v37-mode-llm-status\"",
  "data-testid=\"v37-home-quality-status\"",
  "首页只显示简短 Quality 状态",
  "完整 Quality Gate、Hidden Leak Report 和 Playtest 结果收纳在高级工具",
  "没有项目时，先打开/创建项目或试用 Demo 项目",
  "体验 Demo 项目",
  "examples/demo_local_narrative_project",
  "fake/local_stub provider",
  "试写小说",
  "试角色 RP",
  "试大世界游玩",
  "<SafePathSummary value={project.path_redacted}",
  "暂无最近项目"
], "Chinese playable Home");

for (const token of [
  "Product Readiness Dashboard",
  "StateDelta Viewer",
  "TimelineReplayPanel",
  "EventLogViewerPanel",
  "raw_state_delta",
  "raw state_deltas",
  "hidden fact text",
  "<aside id=\"debug-panel\""
]) {
  forbidToken(homeSlice, token, "default Home debug/developer surface");
}

if (countMatches(homeSlice, /\bdisabled=/g) > 0 || homeSlice.includes("<DisabledState")) {
  failures.push("Chinese playable Home should use contextual next steps instead of rendering disabled controls.");
}

if (homeSlice.includes("project.path}") || homeSlice.includes("workspace.path}") || homeSlice.includes("full_path")) {
  failures.push("Chinese playable Home must use redacted safe path summaries, not raw project paths.");
}

requireToken(app, "async function handleOpenDemoProject", "Demo project one-click handler");
requireToken(app, "await handleAddWorkspace(\"examples/demo_local_narrative_project\", \"Demo Local Narrative Project\")", "Demo project opens through safe workspace reference");
if (/setGameState|applyStateDelta|submitPlayerInput/.test(homeSlice)) {
  failures.push("Chinese playable Home must not directly modify GameState or submit world actions.");
}

const studioHomeSlice = sourceSlice(app, "function StudioHome", "function WorldHealthDashboard", 42000);
const advancedHomeIndex = studioHomeSlice.indexOf("data-testid=\"v37-home-advanced-tools\"");
const readinessIndex = studioHomeSlice.indexOf("<ProductReadinessDashboard");
if (advancedHomeIndex < 0 || readinessIndex < 0 || readinessIndex < advancedHomeIndex) {
  failures.push("Product Readiness Dashboard must stay inside the Advanced Tools foldout, not expanded on the playable Home.");
}
requireToken(studioHomeSlice, "<details className=\"home-advanced-tools\" data-testid=\"v37-home-advanced-tools\">", "Home Advanced Tools foldout");
requireToken(studioHomeSlice, "高级工具与完整检查 / Advanced Tools", "Chinese Advanced Tools foldout label");

const visibleBeforeAdvanced = sourceSlice(app, "function StudioHome", "<details className=\"home-advanced-tools\"");
for (const token of ["Product Readiness Dashboard", "StateDelta Viewer", "TimelineReplayPanel", "EventLogViewerPanel", "raw_state_delta", "raw state_deltas"]) {
  forbidToken(visibleBeforeAdvanced, token, "Studio Home visible-before-advanced debug/developer content");
}

const navSlice = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
requireTokens(navSlice, [
  "data-testid=\"v37-main-nav\"",
  "data-testid=\"v37-common-settings-nav\"",
  "data-testid=\"v37-advanced-tools-nav\"",
  "cnLabel: `${CN_COPY.nav.home} / ${CN_COPY.nav.project}`",
  "cnLabel: CN_COPY.nav.novel",
  "cnLabel: CN_COPY.nav.tavern",
  "cnLabel: CN_COPY.nav.world",
  "cnLabel: CN_COPY.nav.provider",
  "cnLabel: CN_COPY.nav.settings",
  "cnLabel: CN_COPY.nav.backup",
  "<summary>{CN_COPY.nav.advancedTools}</summary>",
  "<span>Debug / Replay</span>",
  "尚未选择项目：只需要先打开/创建项目，或配置模型服务。"
], "Chinese reduced navigation");

const advancedNavIndex = navSlice.indexOf("data-testid=\"v37-advanced-tools-nav\"");
const debugNavIndex = navSlice.indexOf("<span>Debug / Replay</span>");
if (advancedNavIndex < 0 || debugNavIndex < 0 || debugNavIndex < advancedNavIndex) {
  failures.push("Debug / Replay must be inside the Advanced Tools navigation.");
}
requireToken(navSlice, "open={false}", "Advanced Tools navigation collapsed by default");
for (const token of ["api_key", "transient_api_key", "Authorization", "raw provider response"]) {
  forbidToken(navSlice, token, "navigation sensitive/provider raw token");
}

const tourSlice = sourceSlice(app, "function FirstRunOnboardingFlow", "function ModeLandingPage");
requireTokens(tourSlice, [
  "data-testid=\"v37-tour-current-step\"",
  "data-testid=\"v37-tour-all-steps\"",
  "CN_COPY.tour.viewAllSteps",
  "CN_COPY.tour.back",
  "CN_COPY.tour.next",
  "CN_COPY.tour.skip",
  "CN_COPY.tour.finish",
  "{CN_COPY.tour.step} {step + 1} / {PLAYABLE_PRODUCT_TOUR_STEPS.length}"
], "Chinese first-run tour");
requireTokens(app, ["查看全部步骤", "上一步", "下一步", "跳过", "完成"], "Chinese first-run tour copy");
requireToken(tourSlice, "<details className=\"tour-all-steps\" data-testid=\"v37-tour-all-steps\" open={false}>", "all tour steps collapsed by default");
const currentStepIndex = tourSlice.indexOf("data-testid=\"v37-tour-current-step\"");
const allStepsIndex = tourSlice.indexOf("data-testid=\"v37-tour-all-steps\"");
if (currentStepIndex < 0 || allStepsIndex < 0 || allStepsIndex < currentStepIndex) {
  failures.push("First-run tour should show the current step card before the collapsed all-steps list.");
}
for (const token of ["TimelineReplayPanel", "StateDeltaViewerPanel", "EventLogViewerPanel", "Debug Snapshot", "raw_state_delta"]) {
  forbidToken(tourSlice, token, "first-run tour debug/developer token");
}

requireTokens(providerUi, [
  "模型服务设置向导",
  "配置真实 LLM API 或本地模型服务",
  "1. 模型服务类型",
  "服务类型",
  "Base URL 环境变量",
  "临时输入，仅用于本次测试",
  "使用环境变量，例如 OPENAI_API_KEY",
  "使用 secret_ref",
  "使用本地 local_secret_ref",
  "无需 API Key",
  "已保存密钥不会在 UI 中显示",
  "Authorization header 与 provider raw response 也不会渲染",
  "手动添加 model_id",
  "设置 / 隐私 / 模型服务",
  "产品设置分区",
  "常规设置",
  "本地隐私",
  "模型服务",
  "模型分配",
  "备份 / 恢复",
  "诊断",
  "Mature Module / 成人内容模块",
  "UI Preferences / 界面偏好",
  "不提供账号设置、云同步设置、在线市场设置或远程包下载设置"
], "Provider and Settings Chinese UI");

requireTokens(desktopUi, [
  "备份 / 恢复",
  "备份 dry-run",
  "创建本地备份",
  "诊断 / 日志",
  "预览诊断包",
  "创建本地诊断包",
  "不会上传",
  "默认不包含 API key、.env、provider secrets、debug raw data、mature/private",
  "请求失败",
  "建议：重试本地操作，检查后端健康状态，或打开诊断查看脱敏预览"
], "Backup / Diagnostics Chinese UI");

requireTokens(`${app}\n${providerUi}\n${desktopUi}`, [
  "无需账号",
  "不使用云同步",
  "无在线市场"
], "no account / no cloud / no marketplace Chinese notices");

const sourceBundle = `${homeSlice}\n${navSlice}\n${tourSlice}\n${providerUi}\n${desktopUi}`;
if (/<input[^>]+name=["']api_key["']/i.test(sourceBundle)) {
  failures.push("Plaintext api_key input detected in localized UI source.");
}
if (/localStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i.test(sourceBundle)) {
  failures.push("Localized UI must not persist API keys or transient keys to localStorage.");
}
if (/sessionStorage\.setItem\([^)]*(api[_-]?key|transient[_-]?api[_-]?key|Authorization)/i.test(sourceBundle)) {
  failures.push("Localized UI must not persist API keys or transient keys to sessionStorage.");
}
if (/Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{12,}/.test(sourceBundle)) {
  failures.push("Authorization bearer value detected in localized UI source.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(sourceBundle)) {
  failures.push("Secret-looking sk-* token detected in localized UI source.");
}

if (!pkg.scripts?.["check:v37-product-cn"]) {
  failures.push("package.json is missing check:v37-product-cn.");
}

if (failures.length) {
  console.error("v3.7 Chinese product UI check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Chinese product UI check passed.");
