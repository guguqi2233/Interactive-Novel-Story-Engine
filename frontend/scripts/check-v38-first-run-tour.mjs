import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}`);
  }
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}`);
  }
}

function sourceSlice(source, startToken, endToken, fallbackLength = 24000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const tourSlice = sourceSlice(app, "function FirstRunOnboardingFlow", "function ModeLandingPage");
const stepSlice = sourceSlice(app, "const PLAYABLE_PRODUCT_TOUR_STEPS", "function FirstRunOnboardingFlow");

requireToken(app, "const PLAYABLE_PRODUCT_TOUR_STEPS", "7-step playable tour list");
requireToken(tourSlice, "data-testid=\"v38-first-run-tour-shell\"", "simplified tour shell");
requireToken(tourSlice, "data-testid=\"v38-tour-progress\"", "tour progress marker");
requireToken(tourSlice, "data-testid=\"v37-tour-current-step\"", "current step card");
requireToken(tourSlice, "data-testid=\"v37-tour-all-steps\"", "collapsed all steps");
requireToken(tourSlice, "data-testid=\"v38-tour-local-boundary\"", "collapsed local boundary notes");
requireToken(app, "上一步", "Chinese back button");
requireToken(app, "下一步", "Chinese next button");
requireToken(app, "跳过", "Chinese skip button");
requireToken(app, "完成", "Chinese finish button");
requireToken(app, "查看全部步骤", "Chinese all steps summary");
requireToken(stepSlice, "欢迎：本地优先", "step 1");
requireToken(stepSlice, "创建或打开项目", "step 2");
requireToken(stepSlice, "配置模型服务", "step 3");
requireToken(stepSlice, "测试连接并读取模型", "step 4");
requireToken(stepSlice, "按模式分配模型", "step 5");
requireToken(stepSlice, "选择开始方式：写小说 / RP / 大世界", "step 6");
requireToken(stepSlice, "本地备份与隐私说明", "step 7");
requireToken(tourSlice, "可以先跳过模型服务配置", "screen-reader provider skip safety copy");
requireToken(tourSlice, "不会要求输入明文密钥", "plaintext key safety copy");
requireToken(tourSlice, "向导不会修改 GameState", "GameState safety copy");
requireToken(styles, ".first-run-tour-shell", "simplified tour shell style");
requireToken(styles, ".tour-local-boundary", "collapsed local boundary style");
requireToken(pkg.scripts?.["check:v38-first-run-tour"] ?? "", "node scripts/check-v38-first-run-tour.mjs", "package script");

for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "Product Readiness Dashboard",
  "developer checklist",
  "raw_state_delta",
  "testProjectProviderConnection",
  "fetch(",
  "submitPlayerInput",
  "saveGame(",
  "applySaveMigration"
]) {
  forbidToken(tourSlice, token, `tour default implementation token ${token}`);
}

const topBeforeCurrentCard = tourSlice.slice(0, tourSlice.indexOf("data-testid=\"v37-tour-current-step\""));
if ((topBeforeCurrentCard.match(/<SafeSummaryCard/g) ?? []).length > 0) {
  failures.push("First-run tour should not show multiple safety summary cards before the current-step card.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(tourSlice + stepSlice)) {
  failures.push("Secret-looking sk-* token detected in first-run tour.");
}

if (failures.length) {
  console.error("v3.8 first-run tour check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 first-run tour check passed.");
