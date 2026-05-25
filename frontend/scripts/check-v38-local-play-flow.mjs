import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}`);
}

function requireAnyToken(source, tokens, label) {
  if (!tokens.some((token) => source.includes(token))) failures.push(`Missing ${label}`);
}

function requireAbsent(source, token, label = token) {
  if (source.includes(token)) failures.push(`Forbidden ${label}`);
}

const homeStart = app.indexOf("function ChinesePlayableHomePanel");
const homeEnd = app.indexOf("function ProjectHomeRedesignPanel", homeStart);
const home = app.slice(homeStart, homeEnd > homeStart ? homeEnd : undefined);

requireToken(home, "function ChinesePlayableHomePanel", "Chinese playable home panel");
requireToken(home, "buildModeFlow", "local play flow helper");
requireToken(home, "handleModePrimary", "mode primary action router");
requireToken(home, "const novelFlow = buildModeFlow(\"novel\")", "Novel flow");
requireToken(home, "const tavernFlow = buildModeFlow(\"tavern\")", "Tavern flow");
requireToken(home, "const worldFlow = buildModeFlow(\"world\")", "World flow");

for (const token of [
  "写小说",
  "角色 RP",
  "大世界游玩",
  "先打开/创建项目",
  "配置模型服务",
  "分配模型",
  "没有稿件时先创建稿件",
  "创建稿件",
  "没有角色时先创建/导入角色",
  "创建/导入角色",
  "没有存档时先开始新世界",
  "开始新世界",
  "mock/local_stub"
]) {
  requireToken(home, token, `Chinese local play flow copy: ${token}`);
}

requireAnyToken(
  home + app,
  ["API Key 不会显示或保存到项目", "API Key 不保存到项目文件", "API Key 仅保存在本地"],
  "API Key local-only project safety copy"
);

for (const [dataTestId, ...acceptedTokens] of [
  ["data-testid=\"v38-open-novel-card\"", "testId=\"v38-open-novel-card\""],
  ["data-testid=\"v38-open-tavern-card\"", "testId=\"v38-open-tavern-card\""],
  ["data-testid=\"v38-open-world-card\"", "testId=\"v38-open-world-card\""],
  ["data-testid=\"v38-novel-write-chapter\"", "testId=\"v38-novel-write-chapter\"", "primaryTestId=\"v38-novel-write-chapter\""],
  ["data-testid=\"v38-tavern-select-character\"", "testId=\"v38-tavern-select-character\"", "primaryTestId=\"v38-tavern-select-character\""],
  ["data-testid=\"v38-world-continue\"", "testId=\"v38-world-continue\"", "primaryTestId=\"v38-world-continue\""]
]) {
  requireAnyToken(home, [dataTestId, ...acceptedTokens], `mode card test id: ${dataTestId}`);
}

for (const forbidden of ["Authorization:", "Bearer ", "transient_api_key", "npc_knowledge", "debug memory:"]) {
  requireAbsent(home, forbidden, `normal Home forbidden token: ${forbidden}`);
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(home)) {
  failures.push("Home appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-local-play-flow"] ?? "", "node scripts/check-v38-local-play-flow.mjs", "package script");

if (failures.length) {
  console.error("v3.8 local play flow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 local play flow check passed.");
