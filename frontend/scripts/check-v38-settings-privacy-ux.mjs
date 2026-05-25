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

const start = app.indexOf("function SettingsPrivacyPanel");
const end = app.indexOf("function PromptProfileSelector", start);
const settings = app.slice(start, end > start ? end : undefined);

requireToken(settings, "data-testid=\"v38-settings-privacy-overview\"", "settings/privacy overview");
requireToken(settings, "data-testid=\"v38-settings-sections\"", "settings sections grid");
for (const section of [
  "常规",
  "模型服务",
  "模型分配",
  "本地隐私",
  "导出",
  "调试",
  "备份 / 恢复",
  "诊断",
  "Mature Module",
  "界面偏好"
]) {
  requireToken(settings, section, `settings section: ${section}`);
}

for (const token of [
  "不显示 API Key 值",
  "密钥值只在后端",
  "脱敏已启用",
  "Debug 状态由 ENABLE_DEBUG_API 控制",
  "默认关闭",
  "普通导出排除",
  "清空最近项目",
  "查看键盘快捷键",
  "不能写入 .env、不能保存明文 secret、不能新增云功能"
]) {
  requireToken(settings, token, `settings safety copy: ${token}`);
}

for (const forbidden of [
  "账号设置",
  "云同步设置",
  "Cloud Sync Settings",
  "Account Settings",
  "Marketplace Settings",
  "localStorage.setItem(\"api",
  "sessionStorage.setItem(\"api",
  "Authorization:",
  "Bearer ",
  "transient_api_key"
]) {
  requireAbsent(settings, forbidden, `settings forbidden token: ${forbidden}`);
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(settings)) {
  failures.push("Settings slice appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-settings-privacy-ux"] ?? "", "node scripts/check-v38-settings-privacy-ux.mjs", "package script");

if (failures.length) {
  console.error("v3.8 settings/privacy UX check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 settings/privacy UX check passed.");
