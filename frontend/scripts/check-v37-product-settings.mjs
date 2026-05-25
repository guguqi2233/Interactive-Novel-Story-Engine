import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 20000);
}

requireToken(providerUi, "export function SettingsPrivacyPanel", "SettingsPrivacyPanel");
requireToken(providerUi, "const productSettingsSections", "v3.7 product settings section map");
requireToken(providerUi, "产品设置分区", "settings section UI heading");
requireToken(providerUi, "不提供账号设置、云同步设置、在线市场设置", "local-only settings exclusion notice");
requireToken(providerUi, "This form intentionally has no plaintext API key field.", "provider form secret boundary copy");
requireToken(providerUi, "Mature 默认关闭", "mature default-disabled copy");
requireToken(providerUi, "导出默认过滤 API key", "export filtering copy");
requireToken(providerUi, "Debug API is disabled / Debug API 未开启", "debug disabled state copy");
requireToken(providerUi, "模型分配", "provider model settings section");
requireToken(providerUi, "UI Preferences / 界面偏好", "UI preferences settings section");

for (const label of [
  "常规设置",
  "本地隐私",
  "模型服务",
  "模型分配",
  "导出",
  "Debug / 调试",
  "备份 / 恢复",
  "诊断",
  "Mature Module / 成人内容模块",
  "UI Preferences / 界面偏好"
]) {
  requireToken(providerUi, `cnTitle: "${label}"`, `${label} settings section`);
}

const settingsSlice = sourceSlice(providerUi, "const productSettingsSections", "<PromptProfileSafeSettings");
for (const forbidden of [
  "title: \"Account",
  "cnTitle: \"账号",
  "title: \"Cloud",
  "cnTitle: \"云",
  "title: \"Cloud Sync",
  "title: \"Online Marketplace",
  "title: \"Marketplace",
  "title: \"Remote Package Download",
  "Save Plaintext Key",
  "transient_api_key",
  "raw_state_delta",
  "hidden fact text"
]) {
  if (settingsSlice.includes(forbidden)) {
    failures.push(`Settings panel includes forbidden section or sensitive token: ${forbidden}`);
  }
}

if (/draft\.api_key(?!_env)/.test(providerUi)) {
  failures.push("Provider form appears to reference a plaintext api_key field instead of api_key_env.");
}

if (/localStorage\.setItem\([^)]*(api[_-]?key|secret|transient)/i.test(providerUi)) {
  failures.push("Settings/provider UI must not store key-like values in localStorage.");
}

if (/sessionStorage\.setItem\([^)]*(api[_-]?key|secret|transient)/i.test(providerUi)) {
  failures.push("Settings/provider UI must not store key-like values in sessionStorage.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(settingsSlice)) {
  failures.push("Secret-looking sk-* token detected in settings section source.");
}

requireToken(styles, ".settings-section-grid", "settings section grid style");
requireToken(styles, ".settings-section-item", "settings section item style");
requireToken(styles, ".settings-section-heading", "settings section heading style");

if (!pkg.scripts?.["check:v37-product-settings"]) {
  failures.push("package.json is missing check:v37-product-settings.");
}

if (failures.length) {
  console.error("v3.7 product settings check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product settings check passed.");
