import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 28000);
}

requireToken(app, "function ProductStateFinalPolishPanel", "Product state final polish panel");
requireToken(app, "产品错误 / 空状态 / 禁用状态最终收口", "state polish UI heading");
requireToken(app, "空状态包含下一步", "empty state coverage");
requireToken(app, "安全错误包含修复建议", "safe error coverage");
requireToken(app, "禁用状态说明原因", "disabled state coverage");
requireToken(app, "Debug 已禁用：需要 ENABLE_DEBUG_API", "debug disabled guidance");
requireToken(app, "缺少模型服务：配置 api_key_env/secret_ref", "provider missing secret guidance");
requireToken(app, "无账号、无云同步、无在线市场", "local-first state copy");

for (const surface of [
  "项目首页",
  "写小说",
  "角色 RP",
  "大世界",
  "创作 / Mod",
  "模型服务",
  "质量检查 / 调试",
  "备份 / 恢复",
  "诊断",
  "设置"
]) {
  requireToken(app, `surface: "${surface}"`, `${surface} state coverage`);
}

for (const token of [
  "EmptyState",
  "DisabledState",
  "请求失败",
  "建议：",
  "sanitizeDisplayError(message)",
  "普通界面不会显示 stack trace",
  "不显示 stack trace",
  "敏感本地路径",
  "raw state_deltas"
]) {
  requireToken(app, token, `${token} state safety token`);
}

requireToken(providerUi, "建议：重试本地操作，检查模型服务设置，并使用 api_key_env、secret_ref 或 local_secret_ref 处理缺失密钥。", "Provider UI error repair suggestion");
requireToken(desktopUi, "建议：重试本地操作，检查后端健康状态，或打开诊断查看脱敏预览。", "Desktop UI error repair suggestion");
requireToken(styles, ".product-state-grid", "product state grid style");
requireToken(styles, ".product-state-card", "product state card style");
requireToken(styles, ".state-polish-summary", "state polish summary style");

const statePanel = sourceSlice(app, "function ProductStateFinalPolishPanel", "function NovelCompleteWorkflowChecklist");
for (const forbidden of [
  "fetch(",
  "requestJson",
  "testProjectProviderConnection",
  "fetchProjectProviderStatus",
  "createDiagnosticsBundle(",
  "createBackup(",
  "setGameState",
  "applyStateDelta",
  "window.location",
  "localStorage.setItem",
  "sessionStorage.setItem",
  "sk-"
]) {
  if (statePanel.includes(forbidden)) {
    failures.push(`State polish panel includes forbidden active call or secret-like token: ${forbidden}`);
  }
}

if (/Traceback[\s\S]{0,80}<pre>|stack[\s\S]{0,80}<pre>/i.test(statePanel)) {
  failures.push("State polish panel appears to render raw stack trace content.");
}

if (!pkg.scripts?.["check:v37-product-states"]) {
  failures.push("package.json is missing check:v37-product-states.");
}

if (failures.length) {
  console.error("v3.7 product error/empty/disabled state check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product error/empty/disabled state check passed.");
