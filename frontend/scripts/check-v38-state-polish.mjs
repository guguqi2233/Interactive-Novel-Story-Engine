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

function sliceBetween(source, start, end) {
  const startIndex = source.indexOf(start);
  if (startIndex < 0) {
    failures.push(`Missing slice start: ${start}`);
    return "";
  }
  const endIndex = end ? source.indexOf(end, startIndex + start.length) : source.length;
  return source.slice(startIndex, endIndex < 0 ? source.length : endIndex);
}

const stateSlice = sliceBetween(app, "function localizeStateText", "function getSafeApiBaseUrlSummary");
const errorSlice = sliceBetween(app, "function ErrorPanel", "function BackendUnavailableState");
const backendUnavailableSlice = sliceBetween(app, "function BackendUnavailableState", "function localizeStateText");

requireToken(app, "function EmptyState", "EmptyState component");
requireToken(app, "function DisabledState", "DisabledState component");
requireToken(app, "function BackendUnavailableState", "BackendUnavailableState component");
requireToken(app, "function localizeStateText", "localized state text helper");
requireToken(app, "sanitizeDisplayError(message)", "safe ErrorPanel sanitization");
requireToken(app, "sanitizeDisplayError(localizeStateText(title)", "safe localized title sanitization");
requireToken(app, "sanitizeDisplayError(localizeStateText(detail)", "safe localized detail sanitization");
requireToken(app, "data-testid=\"v38-empty-state\"", "v3.8 empty state test id");
requireToken(app, "data-testid=\"v38-disabled-state\"", "v3.8 disabled state test id");
requireToken(app, "BackendUnavailableState", "backend unavailable reuse");
requireToken(app, "Traceback", "stack trace redaction");
requireToken(app, "safeAriaText(displayTitle)", "safe aria labels");

for (const token of [
  "本地后端未连接",
  "重新连接",
  "查看启动指南",
  "打开诊断",
  "打开设置",
  "尚未选择项目",
  "打开/创建项目",
  "配置模型服务",
  "缺少模型服务配置",
  "缺少模型分配",
  "暂无稿件",
  "暂无角色或会话",
  "暂无存档",
  "ENABLE_DEBUG_API",
  "普通 UI 不显示 raw state_deltas",
  "暂无诊断预览",
  "暂无备份或恢复预览",
  "暂无跨模式审查内容",
  "暂无创作包或 Mod 草稿",
  "暂无质量检查结果"
]) {
  requireToken(stateSlice, token, `Chinese state copy: ${token}`);
}

for (const forbidden of [
  "process.env",
  "Authorization:",
  "Bearer ",
  "child_process",
  "exec(",
  "spawn(",
  "console.error(error)",
  "error.stack"
]) {
  if (stateSlice.includes(forbidden) || errorSlice.includes(forbidden) || backendUnavailableSlice.includes(forbidden)) {
    failures.push(`State polish components must not contain forbidden token: ${forbidden}`);
  }
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(app)) {
  failures.push("Frontend source appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-state-polish"] ?? "", "node scripts/check-v38-state-polish.mjs", "package script");

if (failures.length) {
  console.error("v3.8 state polish check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 state polish check passed.");
