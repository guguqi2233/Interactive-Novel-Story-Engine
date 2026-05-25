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
  return source.slice(start, end > start ? end : start + 30000);
}

const listSlice = sourceSlice(providerUi, "function ProviderConnectivityDashboard", "function ProviderModelAssignmentPanel");
const assignmentSlice = sourceSlice(providerUi, "function ProviderModelAssignmentPanel", "function ProviderCapabilityMatrixPanel");

requireToken(providerUi, "data-testid=\"v37-provider-model-list-final\"", "model list final marker");
requireToken(providerUi, "data-testid=\"v37-model-assignment-final\"", "model assignment final marker");
requireToken(api, "patchProjectProviderModels", "manual model patch API");
requireToken(api, "/providers/${encodeURIComponent(providerProfileId)}/models", "provider models patch endpoint");
requireToken(api, "fetchProjectProviderModels", "fetch models API");
requireToken(api, "syncProjectProviderModels", "sync models API");

for (const token of [
  "manual model add saves ModelProfile metadata",
  "patchProjectProviderModels(projectId, profile.provider_profile_id, nextModels)",
  "supports_text: true",
  "supports_json: manualSupportsJson",
  "supports_streaming: manualSupportsStreaming",
  "supports_tools: manualSupportsTools",
  "data-large-provider-model-list=\"windowed\"",
  "safeSearchMatches",
  "capabilityFilter",
  "enabledFilter",
  "useCaseFilter"
]) {
  requireToken(listSlice, token, `model list support ${token}`);
}

for (const useCase of [
  "novel_draft",
  "novel_rewrite",
  "tavern_reply",
  "multi_npc_reply",
  "world_intent_parse",
  "world_narration",
  "cross_mode_draft",
  "memory_summary",
  "quality_eval",
  "cheap_summary"
]) {
  requireToken(providerUi, `value: \"${useCase}\"`, `assignment use case ${useCase}`);
}

for (const token of [
  "PROVIDER_MODEL_ASSIGNMENT_USE_CASES.map",
  "saveProjectProviderModelAssignments(projectId, currentConfig)",
  "validateProjectProviderModelAssignments(projectId, currentConfig)",
  "fallback_provider_id",
  "fallback_model_id",
  "routingUseCaseRequiresJson(item.value)",
  "world_intent_parse",
  "findProviderModel",
  "Provider Gateway 仍是唯一运行时模型入口"
]) {
  requireToken(assignmentSlice, token, `assignment support ${token}`);
}

if (listSlice.includes("Authorization header") && !listSlice.includes("不显示")) {
  failures.push("Model list must not display Authorization header details.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(listSlice + assignmentSlice)) {
  failures.push("Secret-looking sk-* token detected in provider model UI.");
}
if (/localStorage|sessionStorage/.test(listSlice + assignmentSlice)) {
  failures.push("Provider model list/assignment must not use browser storage for secrets.");
}
if (/raw provider response/i.test(listSlice) && !/不会显示|never rendered|excluded/i.test(listSlice)) {
  failures.push("Provider model UI mentions raw provider response without a redaction/exclusion statement.");
}
if (assignmentSlice.includes("dynamic cost optimization") || assignmentSlice.includes("动态成本优化")) {
  failures.push("Provider model assignment must not introduce dynamic cost optimization.");
}
if (!pkg.scripts?.["check:v37-provider-model-final"]) {
  failures.push("package.json is missing check:v37-provider-model-final.");
}

if (failures.length) {
  console.error("v3.7 provider model final check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 provider model final check passed.");
