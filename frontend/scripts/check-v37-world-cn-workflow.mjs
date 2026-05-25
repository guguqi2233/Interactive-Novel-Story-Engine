import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const worldUi = readFileSync(resolve(root, "src", "worldUi.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const [source, token, label] of [
  [app, "本地大世界入口", "Chinese World entry title"],
  [app, "继续大世界", "Continue World CTA"],
  [app, "开始大世界", "Start World CTA"],
  [app, 'data-testid="v37-world-cn-home"', "World Chinese home marker"],
  [app, 'data-testid="v37-world-cn-start-continue"', "World start/continue marker"],
  [app, 'data-testid="v37-world-cn-provider-warning"', "World missing provider marker"],
  [app, "Provider 未配置", "World provider missing warning"],
  [app, "World intent parser 需要 JSON/结构化能力", "World intent parser model copy"],
  [app, "World narrator 只渲染后端确认结果", "World narrator model copy"],
  [worldUi, "行动输入 / 建议行动", "Chinese action input panel"],
  [worldUi, "玩家输入通过 /game/input 提交", "backend action API copy"],
  [worldUi, "LLM 只做意图解析与叙事渲染", "LLM authority boundary copy"],
  [worldUi, "世界输入解析模型", "World intent parser model panel"],
  [worldUi, "世界叙事渲染模型", "World narrator model panel"],
  [worldUi, "模型服务未配置", "World model service missing state"],
  [worldUi, "普通视图只使用 visible_state", "visible_state normal boundary copy"],
  [worldUi, "raw state_deltas 只在 DebugGate 后显示", "DebugGate raw delta copy"],
  [worldUi, "打开 Provider / 模型分配", "Provider assignment CTA"],
  [api, 'requestJson<GameInputResponse>("/game/input"', "game input API client"],
  [api, 'requestJson<StartGameResponse>("/game/start"', "game start API client"],
]) {
  requireToken(source, token, label);
}

if (!pkg.scripts?.["check:v37-world-cn-workflow"]) {
  failures.push("package.json is missing check:v37-world-cn-workflow.");
}

const combined = `${app}\n${worldUi}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(combined)) {
  failures.push("Secret-looking sk-* token detected in World Chinese workflow frontend source.");
}

if (/<input[^>]+(?:name|id)=["']api[_-]?key["']/i.test(combined)) {
  failures.push("World Chinese workflow must not include plaintext API key inputs.");
}

const normalWorldUi = worldUi.split("export function DebugGate", 1)[0];
if (/JSON\.stringify\(event\.state_deltas/i.test(normalWorldUi)) {
  failures.push("World normal UI renders raw state_deltas before DebugGate.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|OnlinePlaySession)/i.test(combined)) {
  failures.push("Online/account/cloud/marketplace/online-play entrypoint detected in World Chinese workflow source.");
}

if (failures.length) {
  console.error("v3.7 World Chinese workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 World Chinese workflow check passed.");
