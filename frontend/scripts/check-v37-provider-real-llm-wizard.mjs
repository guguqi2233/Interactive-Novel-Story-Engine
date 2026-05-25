import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 26000);
}

const wizardSlice = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");
const saveSlice = sourceSlice(providerUi, "function cleanProviderDraft", "async function validateProvider");

requireToken(providerUi, "function ProviderSetupWizard", "Provider setup wizard component");
requireToken(providerUi, "data-testid=\"v37-provider-real-llm-wizard\"", "Provider wizard test id");
requireToken(providerUi, "模型服务设置向导", "Chinese wizard title");
requireToken(providerUi, "选择模型服务", "Chinese provider type step");
requireToken(providerUi, "临时输入，仅用于本次测试", "transient key mode copy");
requireToken(providerUi, "使用环境变量，例如 OPENAI_API_KEY", "env key mode copy");
requireToken(providerUi, "使用本地 local_secret_ref", "local secret ref mode copy");
requireToken(providerUi, "不允许保存明文 API Key", "plaintext key safety copy");
requireToken(providerUi, "本次点击允许连接真实 Provider", "manual real provider opt-in");
requireToken(providerUi, "读取模型列表", "fetch model list CTA");
requireToken(providerUi, "同步为 ModelProfile", "sync model CTA");
requireToken(providerUi, "手动添加 model_id", "manual model add");
requireToken(providerUi, "按模式分配模型", "mode assignment copy");
requireToken(providerUi, "中转站 / Relay 只表示兼容 API 的 base URL 配置", "relay no-resale copy");
requireToken(providerUi, "type=\"password\"", "masked transient key input");
requireToken(providerUi, "autoComplete=\"off\"", "transient key autocomplete disabled");
requireToken(providerUi, "transientKeyRef", "transient key kept out of React persistent state");
requireToken(api, "ProviderConnectionTestPayload", "connection payload type");
requireToken(api, "ProviderModelFetchPayload", "model fetch payload type");
requireToken(api, "fetchProjectProviderModels", "fetch models API client");
requireToken(api, "syncProjectProviderModels", "sync models API client");

for (const providerType of ["openai", "openai_compatible", "relay", "local_http", "custom", "mock", "local_stub"]) {
  requireToken(providerUi, `value: \"${providerType}\"`, `provider type ${providerType}`);
}

for (const statusCopy of ["未配置", "已配置，未测试", "连接成功", "认证失败", "缺少 API key", "Base URL 无效", "模型列表读取失败", "Provider 不支持模型列表", "超时"]) {
  requireToken(providerUi, statusCopy, `Chinese status ${statusCopy}`);
}

if (/\b(localStorage|sessionStorage)\.(setItem|getItem)|window\.(localStorage|sessionStorage)/.test(wizardSlice)) {
  failures.push("Provider wizard must not use browser storage APIs for API keys.");
}
if (wizardSlice.includes("Authorization header") && !wizardSlice.includes("不会渲染")) {
  failures.push("Provider wizard must not display Authorization header details.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(wizardSlice)) {
  failures.push("Provider wizard contains a secret-looking sk-* token.");
}
if (saveSlice.includes("transient_api_key")) {
  failures.push("Provider profile save path must not persist transient_api_key.");
}
if (!wizardSlice.includes("allow_real_connection: allowRealProviderCall") || !wizardSlice.includes("allow_real_provider: allowRealProviderCall")) {
  failures.push("Real provider calls must require explicit wizard opt-in.");
}
if (!wizardSlice.includes("testProjectProviderConnection(projectId, draft.provider_profile_id, payload)")) {
  failures.push("Wizard must test connection through the safe Provider API client.");
}
if (!wizardSlice.includes("fetchProjectProviderModels(projectId, payload)") || !wizardSlice.includes("syncProjectProviderModels(projectId, payload)")) {
  failures.push("Wizard must expose fake-safe fetch and sync model flows.");
}

if (!pkg.scripts?.["check:v37-provider-real-llm-wizard"]) {
  failures.push("package.json is missing check:v37-provider-real-llm-wizard.");
}

if (failures.length) {
  console.error("v3.7 provider real LLM wizard check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 provider real LLM wizard check passed.");
