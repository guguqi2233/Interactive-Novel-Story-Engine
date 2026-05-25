import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidToken(source, token, label) {
  if (source.includes(token)) failures.push(`Forbidden ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 30000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const homeSlice = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");

requireToken(app, "function ChinesePlayableHomePanel", "Chinese product Home component");
requireToken(homeSlice, "data-testid=\"v37-cn-playable-home\"", "Chinese Home root");
requireToken(homeSlice, "data-testid=\"v38-three-main-mode-cards\"", "v3.8 three main mode cards");
requireToken(app, "function MainModeCard", "MainModeCard component");
requireToken(homeSlice, "testId=\"v38-open-novel-card\"", "Novel large card");
requireToken(homeSlice, "testId=\"v38-open-tavern-card\"", "Tavern large card");
requireToken(homeSlice, "testId=\"v38-open-world-card\"", "World large card");
requireToken(homeSlice, "写小说", "Novel mode Chinese title");
requireToken(homeSlice, "角色 RP", "Tavern mode Chinese title");
requireToken(homeSlice, "大世界游玩", "World mode Chinese title");
requireToken(app, "当前状态", "mode status field");
requireToken(app, "下一步建议", "next action field");
requireToken(app, "最近内容", "recent content field");
requireToken(app, "Provider 模型状态", "provider model status field");
requireToken(homeSlice, "最近稿件", "Novel recent manuscript copy");
requireToken(homeSlice, "写章节", "Novel write chapter action");
requireToken(homeSlice, "打开小说工作室", "Novel studio action");
requireToken(homeSlice, "最近 RP 会话", "Tavern recent session copy");
requireToken(app, "选择角色", "Tavern choose character action");
requireToken(homeSlice, "开始 RP", "Tavern start RP action");
requireToken(homeSlice, "当前世界 / 存档", "World save/current world copy");
requireToken(homeSlice, "继续大世界", "World continue action");
requireToken(homeSlice, "开始大世界", "World start action");
requireToken(homeSlice, "打开/创建项目后可用", "missing project mode availability");
requireToken(homeSlice, "配置模型服务", "model service CTA copy");
requireToken(app, "function ProductCTAGroup", "ProductCTAGroup component");
requireToken(app, "data-testid=\"cn-open-project\"", "open project CTA");
requireToken(app, "data-testid=\"cn-create-project\"", "create project CTA");
requireToken(app, "data-testid=\"cn-configure-provider\"", "configure provider CTA");
requireToken(app, "function ProviderMissingState", "ProviderMissingState component");
requireToken(app, "data-testid=\"v38-provider-missing-cta\"", "provider missing next-step card");
requireToken(app, "data-testid=\"v38-backend-unavailable-state\"", "backend unavailable recovery card");
requireToken(app, "data-testid=\"v38-backend-reconnect\"", "reconnect backend CTA");
requireToken(app, "data-testid=\"v38-backend-startup-guide\"", "startup guide CTA");
requireToken(app, "data-testid=\"v38-backend-open-diagnostics\"", "diagnostics CTA");
requireToken(app, "data-testid=\"v38-backend-open-settings\"", "settings CTA");
requireToken(app, "本地后端未连接", "backend unavailable Chinese title");
requireToken(app, "重新连接", "reconnect Chinese copy");
requireToken(app, "查看启动指南", "startup guide Chinese copy");
requireToken(app, "打开诊断", "diagnostics Chinese copy");
requireToken(app, "打开设置", "settings Chinese copy");
requireToken(app, "raw env", "backend recovery raw env redaction copy");
requireToken(app, "stack trace", "backend recovery stack trace redaction copy");
requireToken(app, "敏感路径", "backend recovery sensitive path redaction copy");
requireToken(app, "API Key", "backend recovery API key redaction copy");
requireToken(app, "API Key 不会显示或保存到项目", "provider key safety copy");

for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "Product Readiness Dashboard",
  "raw_state_delta",
  "<pre>{JSON.stringify(event.state_deltas",
  "<aside id=\"debug-panel\""
]) {
  forbidToken(homeSlice, token, "default Home debug/developer surface");
}

if ((homeSlice.match(/\bdisabled=/g) ?? []).length > 0 || homeSlice.includes("<DisabledState")) {
  failures.push("Product Home should use contextual next steps instead of a disabled-button wall.");
}

requireToken(styles, ".cn-mode-entry-grid-primary", "three-card grid style");
requireToken(styles, ".cn-mode-entry-featured", "featured main mode card style");
requireToken(styles, ".cn-main-mode-card", "structured main mode card style");
requireToken(styles, ".cn-mode-card-meta", "main mode card metadata style");
requireToken(styles, ".backend-unavailable-state", "backend unavailable recovery style");
requireToken(styles, ".provider-next-step-card", "provider next-step style");

if (!pkg.scripts?.["check:v38-product-home"]) {
  failures.push("package.json is missing check:v38-product-home.");
}

if (failures.length) {
  console.error("v3.8 Product Home UX check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 Product Home UX check passed.");
