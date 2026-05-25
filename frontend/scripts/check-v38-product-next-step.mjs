import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}`);
  }
}

function requireAbsent(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}`);
  }
}

const helperStart = app.indexOf("type HomeNextStepKind");
const homeStart = app.indexOf("function ChinesePlayableHomePanel");
const homeEnd = app.indexOf("function ProjectHomeRedesignPanel", homeStart);
const helperAndHome = app.slice(helperStart, homeEnd > homeStart ? homeEnd : undefined);

requireToken(helperAndHome, "type HomeNextStepKind", "typed next step state");
requireToken(helperAndHome, "function buildHomeProviderNextStepSignals", "provider next-step signals helper");
requireToken(helperAndHome, "function buildHomeNextStep", "home next-step resolver");
requireToken(helperAndHome, "data-testid=\"v38-next-step-panel\"", "next-step panel");
requireToken(helperAndHome, "data-testid=\"v38-next-step-action\"", "next-step action");

for (const token of [
  "missing_project",
  "missing_provider",
  "provider_not_tested",
  "missing_model_list",
  "missing_model_assignment",
  "missing_novel_manuscript",
  "missing_tavern_character",
  "missing_world_save",
  "ready",
  "打开/创建项目",
  "配置模型服务",
  "测试连接",
  "读取模型或手动添加模型",
  "按模式分配模型",
  "创建稿件",
  "创建/导入角色",
  "开始大世界",
  "继续写作 / RP / 游玩",
  "首页不会自动调用真实 provider",
  "不会显示或保存到项目",
  "hasProviderTested",
  "hasModelList",
  "hasModelAssignment"
]) {
  requireToken(helperAndHome, token, `next-step rule/copy: ${token}`);
}

for (const forbidden of [
  "fetch(",
  "testConnection(",
  "applyDelta(",
  "state_deltas:",
  "Authorization:",
  "Bearer ",
  "transient_api_key",
  "localStorage.setItem"
]) {
  requireAbsent(helperAndHome, forbidden, `next-step side effect or secret token: ${forbidden}`);
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(helperAndHome)) {
  failures.push("Next-step UI appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-product-next-step"] ?? "", "node scripts/check-v38-product-next-step.mjs", "package script");

if (failures.length) {
  console.error("v3.8 Product Status / Next Step UX check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 Product Status / Next Step UX check passed.");
