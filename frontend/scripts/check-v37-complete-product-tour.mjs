import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
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
  return source.slice(start, end > start ? end : start + 18000);
}

requireToken(app, "const COMPLETE_PRODUCT_TOUR_STEPS", "complete product tour legacy step list");
requireToken(app, "const PLAYABLE_PRODUCT_TOUR_STEPS", "simplified playable product tour step list");
requireToken(app, "function FirstRunOnboardingFlow", "first-run tour component");
requireToken(app, "首次使用向导", "Chinese tour title");
requireToken(app, "打开首次使用向导", "reopen product tour button");
requireToken(app, "function reopenFirstRunOnboarding", "tour reopen handler");
requireToken(app, "removeItem(FIRST_RUN_ONBOARDING_KEY)", "local skip/completion reset");
requireToken(app, "跳过", "skip button");
requireToken(app, "完成", "finish button");
requireToken(app, "向导只在本地记录完成/跳过状态", "local-only tour storage copy");

for (const title of [
  "欢迎：本地优先",
  "创建或打开项目",
  "配置模型服务",
  "测试连接并读取模型",
  "按模式分配模型",
  "选择开始方式：写小说 / RP / 大世界",
  "本地备份与隐私说明"
]) {
  requireToken(app, `title: "${title}"`, `${title} tour step`);
}

for (const copy of [
  "无需账号",
  "不使用云同步",
  "无在线市场",
  "远程包下载",
  "Provider setup can be skipped",
  "The tour never asks for a plaintext key",
  "真实连接只由用户手动触发",
  "向导不会修改 GameState",
  "遥测"
]) {
  requireToken(app, copy, `${copy} safety copy`);
}

const tour = sourceSlice(app, "function FirstRunOnboardingFlow", "function ModeLandingPage");
if (tour.includes("fetch(") || tour.includes("requestJson") || tour.includes("testProjectProviderConnection")) {
  failures.push("First-run product tour must not call network/provider APIs.");
}
if (tour.includes("submitPlayerInput") || tour.includes("saveGame(") || tour.includes("applySaveMigration")) {
  failures.push("First-run product tour must not modify GameState.");
}
if (tour.includes("api_key") && !tour.includes("api_key_env")) {
  failures.push("Tour should mention api_key_env/secret_ref boundaries, not plaintext api_key fields.");
}

requireToken(styles, ".product-tour-steps", "tour step list styles");
requireToken(styles, ".product-tour-step-panel", "tour step panel styles");
requireToken(styles, ".secondary-action", "reopen tour button styles");
requireToken(styles, ".first-run-tour-shell", "simplified tour shell styles");

if (!pkg.scripts?.["check:v37-complete-product-tour"]) {
  failures.push("package.json is missing check:v37-complete-product-tour.");
}

const sourceBundle = `${app}\n${styles}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(sourceBundle)) {
  failures.push("Secret-looking sk-* token detected in v3.7 tour source.");
}
if (/<input[^>]+name=["']api_key["']/i.test(sourceBundle)) {
  failures.push("Plaintext api_key input detected in frontend UI.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i.test(sourceBundle)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected.");
}

if (failures.length) {
  console.error("v3.7 complete product tour check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 complete product tour check passed.");
