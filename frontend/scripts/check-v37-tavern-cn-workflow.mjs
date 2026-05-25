import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const tavernUi = readFileSync(resolve(root, "src", "tavernUi.tsx"), "utf8");
const backend = readFileSync(resolve(root, "..", "backend", "app", "main.py"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

for (const [source, token, label] of [
  [app, "Tavern / 角色 RP 工作室", "Chinese Tavern page title"],
  [app, "配置模型服务", "Provider missing CTA"],
  [app, "使用真实 LLM 前确认当前模型", "current model before LLM notice"],
  [app, "发送 RP / 生成回复", "single-character RP action"],
  [app, "开始多 NPC 场景", "multi-NPC entry"],
  [app, "Tavern 回复已通过 ProviderGateway", "ProviderGateway reply status"],
  [app, "Tavern UI does not modify World GameState", "GameState boundary copy"],
  [app, "Mature Module is disabled by default", "mature default-off copy"],
  [app, 'data-testid="v37-tavern-cn-chat-actions"', "Chinese Tavern chat action marker"],
  [app, 'data-testid="v37-tavern-cn-provider-status"', "Chinese Tavern provider status marker"],
  [tavernUi, "单角色 RP", "single-character chat Chinese UI"],
  [tavernUi, "多 NPC 场景", "multi-NPC Chinese UI"],
  [tavernUi, "RP 记忆 / 关系摘要", "RP memory Chinese UI"],
  [tavernUi, "情绪弧线", "emotion panel Chinese UI"],
  [tavernUi, "关系语气", "relationship panel Chinese UI"],
  [tavernUi, "运行 RP Safety", "RP safety Chinese action"],
  [tavernUi, "Tavern → World", "Tavern to World proposal boundary"],
  [tavernUi, "Tavern → Novel", "Tavern to Novel draft boundary"],
  [tavernUi, "NPC secrets", "NPC secret exclusion copy"],
  [tavernUi, "mature/private memory", "mature/private exclusion copy"],
  [backend, "ProviderRoutingUseCase.TAVERN_REPLY", "Tavern provider routing use case"],
  [backend, "FakeLLMProvider", "fake provider test/runtime fallback"],
]) {
  requireToken(source, token, label);
}

if (!pkg.scripts?.["check:v37-tavern-cn-workflow"]) {
  failures.push("package.json is missing check:v37-tavern-cn-workflow.");
}

const tavernSource = `${app}\n${tavernUi}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(tavernSource)) {
  failures.push("Secret-looking sk-* token detected in Tavern Chinese workflow source.");
}

const homeSlice = app.slice(app.indexOf("Tavern / 角色 RP 工作室"), app.indexOf("<section className=\"tool-card\">", app.indexOf("Tavern / 角色 RP 工作室") + 1));
if (/Authorization header|transient_api_key/i.test(homeSlice)) {
  failures.push("Tavern normal workflow slice contains raw debug/provider secret terminology.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|MultiplayerRoom)/i.test(tavernSource)) {
  failures.push("Online/account/cloud/marketplace/multiplayer entrypoint detected in Tavern workflow frontend source.");
}

if (failures.length) {
  console.error("v3.7 Tavern Chinese workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Tavern Chinese workflow check passed.");
