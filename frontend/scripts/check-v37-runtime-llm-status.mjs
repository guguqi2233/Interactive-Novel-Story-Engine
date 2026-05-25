import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
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

const homeSlice = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const runtimeHelperSlice = sourceSlice(app, "function buildHomeLlmRuntimeStatus", "function ChinesePlayableHomePanel");
const wizardSlice = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");
const dashboardSlice = sourceSlice(providerUi, "function ProviderConnectivityDashboard", "function ProviderSetupChecklistPanel");

requireToken(app, "function buildHomeLlmRuntimeStatus", "home runtime LLM status helper");
requireToken(app, "data-testid=\"v37-runtime-llm-status\"", "runtime LLM status panel");
requireToken(app, "data-testid=\"v37-home-model-service-status\"", "home model service status grid");
requireToken(app, "data-testid=\"v37-mode-llm-status\"", "Novel/Tavern/World mode LLM status");
requireToken(app, "\u6a21\u578b\u670d\u52a1\u72b6\u6001", "Chinese model service status copy");
requireToken(app, "\u5f53\u524d\u662f\u5426\u4f7f\u7528\u771f\u5b9e LLM", "Chinese real LLM status copy");
requireToken(app, "provider connected / \u8fde\u63a5\u6210\u529f", "connected status copy");
requireToken(app, "\u6a21\u578b\u5df2\u914d\u7f6e", "model configured copy");
requireToken(app, "\u6a21\u578b\u7f3a\u5931", "missing model copy");
requireToken(app, "provider \u672a\u8fde\u63a5", "provider disconnected copy");
requireToken(app, "\u4f7f\u7528 mock/local_stub", "mock/local_stub status copy");
requireToken(app, "\u542f\u52a8\u548c\u9996\u9875\u4e0d\u4f1a\u81ea\u52a8\u8054\u7f51", "no startup real-network copy");
requireToken(app, "safeApiCacheStatuses", "safe cache status source");
requireToken(app, "Provider \u72b6\u6001\u7f13\u5b58", "safe provider cache wording");
requireToken(providerUi, "data-testid=\"v37-provider-wizard-manual-test\"", "wizard manual test button");
requireToken(providerUi, "data-testid=\"v37-provider-manual-test-safe-hint\"", "wizard manual safe hint");
requireToken(providerUi, "data-testid=\"v37-manual-provider-test-connection\"", "provider dashboard manual test button");
requireToken(providerUi, "allow_real_connection: allowRealProviderCall", "manual real connection opt-in payload");
requireToken(providerUi, "allow_real_provider: allowRealProviderCall", "manual model fetch opt-in payload");

for (const token of ["testProjectProviderConnection(", "fetchProjectProviderModels(", "syncProjectProviderModels("]) {
  if (homeSlice.includes(token) || runtimeHelperSlice.includes(token)) {
    failures.push(`Home/runtime status must not call provider network API automatically: ${token}`);
  }
}

for (const token of ["api_key", "transient_api_key", "Authorization", "raw provider error", "raw provider response"]) {
  if (homeSlice.includes(`<pre>{${token}`) || runtimeHelperSlice.includes(`<pre>{${token}`)) {
    failures.push(`Runtime status must not render sensitive provider token: ${token}`);
  }
}

if (/\b(localStorage|sessionStorage)\.(setItem|getItem)|window\.(localStorage|sessionStorage)/.test(homeSlice + runtimeHelperSlice + wizardSlice)) {
  failures.push("Runtime LLM status and Provider wizard must not store API keys in browser storage.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(homeSlice + runtimeHelperSlice + wizardSlice + dashboardSlice)) {
  failures.push("Secret-looking sk-* token detected in runtime LLM/provider UI.");
}

if (!wizardSlice.includes("\u53ea\u6709\u7528\u6237\u70b9\u51fb\u6d4b\u8bd5\u8fde\u63a5\u65f6\u624d\u4f1a\u8fde\u63a5\u771f\u5b9e Provider")) {
  failures.push("Provider wizard must state real provider tests are user-triggered only.");
}

if (!pkg.scripts?.["check:v37-runtime-llm-status"]) {
  failures.push("package.json is missing check:v37-runtime-llm-status.");
}

if (failures.length) {
  console.error("v3.7 runtime LLM status check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 runtime LLM status check passed.");
