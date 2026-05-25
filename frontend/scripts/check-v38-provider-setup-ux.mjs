import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 36000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const wizard = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");

requireToken(providerUi, "function ProviderSetupWizard", "Provider setup wizard component");
requireToken(providerUi, "data-testid=\"v37-provider-real-llm-wizard\"", "Provider wizard test id");
requireToken(wizard, "data-testid=\"v38-provider-setup-explainer\"", "v3.8 provider setup explainer");
requireToken(wizard, "模型服务设置向导", "Chinese wizard title");
requireToken(wizard, "选择模型服务类型", "step 1");
requireToken(wizard, "填写 Base URL", "base URL flow step");
requireToken(wizard, "选择 API Key 保存方式", "API key storage flow step");
requireToken(wizard, "测试连接", "test connection step");
requireToken(wizard, "读取模型", "fetch models step");
requireToken(wizard, "分配模型", "assign models step");
requireToken(wizard, "完成", "finish step");
requireToken(wizard, "什么是 Base URL", "base URL explanation");
requireToken(wizard, "什么是 API Key", "API key explanation");
requireToken(wizard, "环境变量 / secret_ref", "env secret_ref explanation");
requireToken(wizard, "为什么要读取模型", "model discovery explanation");
requireToken(wizard, "为什么分配不同模型", "model assignment explanation");
requireToken(wizard, "可能产生费用", "cost warning");
requireToken(wizard, "测试 / CI 仍使用 fake provider", "CI fake provider statement");
requireToken(providerUi, "OpenAI", "OpenAI provider type");
requireToken(providerUi, "OpenAI-compatible", "compatible provider type");
requireToken(providerUi, "中转站 / Relay", "relay provider type");
requireToken(providerUi, "本地模型服务", "local model provider type");
requireToken(providerUi, "自定义 API", "custom provider type");
requireToken(providerUi, "Mock / 测试", "mock provider type");
requireToken(wizard, "临时输入，仅用于本次测试", "transient key mode");
requireToken(wizard, "使用环境变量，例如 OPENAI_API_KEY", "env key mode");
requireToken(wizard, "使用 secret_ref", "secret ref mode");
requireToken(wizard, "使用本地 local_secret_ref", "local secret ref mode");
requireToken(wizard, "手动添加 model_id", "manual model id entry");
requireToken(wizard, "不保存明文 API Key", "plaintext key safety");
requireToken(wizard, "不是 API 转售服务", "no API resale copy");
requireToken(wizard, "type=\"password\"", "masked transient key input");
requireToken(wizard, "autoComplete=\"off\"", "transient key autocomplete disabled");
requireToken(wizard, "transientKeyRef", "transient key ref not persistent state");
requireToken(wizard, "providerStatusToChinese", "friendly status localization");
requireToken(styles, ".provider-setup-explainer", "explainer style");
requireToken(styles, ".provider-explainer-grid", "explainer grid style");
requireToken(pkg.scripts?.["check:v38-provider-setup-ux"] ?? "", "node scripts/check-v38-provider-setup-ux.mjs", "package script");

if (/\b(localStorage|sessionStorage)\.(setItem|getItem)|window\.(localStorage|sessionStorage)/.test(wizard)) {
  failures.push("Provider wizard must not use browser storage APIs for API keys.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(wizard)) {
  failures.push("Provider wizard contains a secret-looking sk-* token.");
}
if (wizard.includes("Authorization header") && !wizard.includes("不会渲染")) {
  failures.push("Provider wizard must only mention Authorization header as hidden/redacted.");
}
if (!wizard.includes("allow_real_connection: allowRealProviderCall") || !wizard.includes("allow_real_provider: allowRealProviderCall")) {
  failures.push("Real provider calls must require explicit wizard opt-in.");
}

if (failures.length) {
  console.error("v3.8 provider setup UX check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 provider setup UX check passed.");
