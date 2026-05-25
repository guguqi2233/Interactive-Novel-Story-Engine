import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}`);
  }
}

requireToken(api, "export const API_BASE_URL", "exported safe API base URL");
requireToken(app, "function BackendUnavailableState", "BackendUnavailableState component");
requireToken(app, "data-testid=\"v38-backend-unavailable-state\"", "backend unavailable test id");
requireToken(app, "本地后端未连接", "Chinese backend unavailable title");
requireToken(app, "当前 API 地址", "current API address summary");
requireToken(app, "可能原因", "possible reasons summary");
requireToken(app, "重新连接", "reconnect button copy");
requireToken(app, "查看启动指南", "startup guide button copy");
requireToken(app, "打开诊断", "diagnostics button copy");
requireToken(app, "打开设置", "settings button copy");
requireToken(app, "getSafeApiBaseUrlSummary", "safe API base URL helper");
requireToken(app, "sanitizeDisplayError(message ||", "backend unavailable sanitization");
requireToken(app, "ErrorPanel", "ErrorPanel integration");
requireToken(app, "isBackendUnavailableMessage(message)", "backend unavailable detection in ErrorPanel");
requireToken(app, "BackendUnavailableState", "BackendUnavailableState reuse");
requireToken(styles, ".backend-unavailable-state", "backend unavailable styles");
requireToken(styles, ".backend-unavailable-header", "backend unavailable header styles");
requireToken(pkg.scripts?.["check:v38-backend-unavailable"] ?? "", "node scripts/check-v38-backend-unavailable.mjs", "package script");

const forbiddenComponentSlice = app.slice(app.indexOf("function BackendUnavailableState"), app.indexOf("function getSafeApiBaseUrlSummary"));
for (const forbidden of [
  "process.env",
  "Authorization:",
  "Bearer ",
  "sk-",
  "state_deltas.map",
  "raw_state_delta",
  "exec(",
  "spawn(",
  "child_process"
]) {
  if (forbiddenComponentSlice.includes(forbidden)) {
    failures.push(`BackendUnavailableState must not contain forbidden token: ${forbidden}`);
  }
}

if (failures.length) {
  console.error("v3.8 backend unavailable recovery check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 backend unavailable recovery check passed.");
