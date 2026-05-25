import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const tavernUi = readFileSync(resolve(root, "src", "tavernUi.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 26000);
}

requireToken(app, "function CrossModeWorkflowClosureChecklist", "Cross-Mode Workflow Closure component");
requireToken(app, "data-v37-cross-mode-workflow-check=\"safe-summary\"", "v3.7 Cross-Mode workflow safe summary marker");
requireToken(app, "buildCrossModeWorkflowClosureChecklistItems", "Cross-Mode checklist builder");
requireToken(app, "跨模式就绪状态", "Product dashboard Cross-Mode readiness item");
requireToken(app, "跨模式工作流闭环", "Chinese Cross-Mode workflow title");
requireToken(app, "不会自动 apply", "no auto apply boundary copy");
requireToken(app, "不会绕过 validation", "validation boundary copy");
requireToken(app, "不会云协作", "no cloud collaboration boundary copy");
requireToken(app, "不会让草稿直接修改 GameState", "draft GameState boundary copy");
requireToken(app, "普通审查也不会显示 hidden details", "hidden detail exclusion copy");
requireToken(app, "validation / dry-run / explicit confirm", "apply requires confirm copy");
requireToken(app, "hidden target details", "hidden target detail redaction copy");

for (const label of [
  "Novel → World 草稿 / 提案可用",
  "World → Novel 章节 / 场景草稿可用",
  "Tavern → World 提案可用",
  "Tavern → Novel 场景草稿可用",
  "World NPC → Tavern 角色草稿可用",
  "CrossMode 本地验证可用",
  "Apply 必须显式确认",
  "CrossMode 审计记录可用",
  "冲突审查可用",
  "默认过滤 hidden / mature / private",
  "草稿不会直接修改 GameState"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const token of [
  "createNovelToWorldDraft",
  "validateNovelToWorldDraft",
  "previewWorldToNovel",
  "adaptWorldNpcToTavern",
  "validateCrossMode",
  "fetchCrossModeAudit",
  "detectCrossModeConflicts",
  "buildTavernApplyPlan",
  "CrossModeDraftSummary",
  "CrossModeConflictReport",
  "CrossModeAuditRecord"
]) {
  requireToken(app, token, `${token} App integration`);
  requireToken(api, token, `${token} API contract`);
}

requireToken(app, "confirmDangerousAction(\"确认从这个 World NPC 创建 Tavern 角色草稿？", "World NPC -> Tavern confirm path");
requireToken(app, "Apply 计划必须显式确认；UI 不会直接修改 World state", "Tavern -> World apply review confirm copy");
requireToken(app, "只用于审查：不会写入 content packs，也不会修改 GameState。", "Novel -> World draft no GameState mutation copy");
requireToken(app, "预览只显示 safe summary，不会修改 World EventLog 或 GameState。", "World -> Novel no mutation copy");
requireToken(app, "普通报告不显示 hidden facts、NPC secrets、debug memory、raw env、API Key 或 raw state_deltas。", "Cross-Mode normal report redaction copy");
requireToken(app, "跨模式桥接 / Cross-Mode Bridge", "Chinese Cross-Mode page title");
requireToken(app, "草稿（draft）、提案（proposal）、审查（review）、验证报告（validation report）和审计记录（audit record）", "draft/proposal/validation/apply explanation");
requireToken(app, "跨模式冲突审查", "Chinese conflict review title");
requireToken(app, "标记已审查", "mark reviewed Chinese button");
requireToken(app, "创建修复草稿", "create fix draft Chinese button");
requireToken(app, "跳转到来源 / 目标", "jump source target Chinese button");
requireToken(tavernUi, "Tavern → World", "Tavern -> World UI copy");
requireToken(tavernUi, "Tavern → Novel", "Tavern -> Novel UI copy");
requireToken(tavernUi, "World NPC → Tavern", "World NPC -> Tavern UI copy");

const checklist = sourceSlice(app, "function CrossModeWorkflowClosureChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "createNovelToWorldDraft(",
  "validateNovelToWorldDraft(",
  "previewWorldToNovel(",
  "adaptWorldNpcToTavern(",
  "validateCrossMode(",
  "detectCrossModeConflicts(",
  "fetchCrossModeAudit(",
  "buildTavernApplyPlan(",
  "applyCrossMode",
  "applyTavernProposal",
  "submitPlayerInput(",
  "saveGame(",
  "applyStateDelta",
  "setVisibleState(",
  "setGameState(",
  "fetch("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Cross-Mode workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("Cross-Mode workflow checklist includes API-key input or transient key terminology outside safe exclusion copy.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${api}\n${tavernUi}`)) {
  failures.push("Secret-looking sk-* token detected in Cross-Mode workflow source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|CloudCollaboration)/i.test(`${app}\n${api}\n${tavernUi}`)) {
  failures.push("Online/account/cloud/marketplace/collaboration enabling entrypoint detected in Cross-Mode workflow source.");
}

if (!pkg.scripts?.["check:v37-cross-mode-workflow"]) {
  failures.push("package.json is missing check:v37-cross-mode-workflow.");
}

if (failures.length) {
  console.error("v3.7 Cross-Mode workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Cross-Mode workflow check passed.");
