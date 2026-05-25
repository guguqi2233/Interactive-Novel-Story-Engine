import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const repoRoot = resolve(root, "..");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const service = readFileSync(resolve(repoRoot, "backend", "app", "platform", "provider_setup_checklist.py"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 12000);
}

requireToken(providerUi, "function ProviderCompleteSetupChecklist", "Provider Complete Setup Checklist component");
requireToken(providerUi, "data-v37-provider-setup-checklist=\"safe-summary\"", "safe summary marker");
requireToken(providerUi, "Provider Complete Setup Checklist", "checklist title");
requireToken(providerUi, "one-time test keys", "transient key safe copy");
requireToken(providerUi, "onJump(item.jump_target)", "jump action");
requireToken(providerUi, "redactProviderChecklistText(item.safe_summary)", "safe summary redaction");
requireToken(providerUi, "redactProviderChecklistText(item.next_action)", "next action redaction");
requireToken(api, "ProviderSetupChecklistReport", "Provider setup checklist API type");
requireToken(api, "/providers/setup-checklist", "Provider setup checklist endpoint");

for (const label of [
  "Provider profile exists",
  "Secret configured via api_key_env, secret_ref, or local_secret_ref",
  "Connection tested",
  "Models fetched or manually added",
  "ModelProfile synced",
  "Novel model assigned",
  "Tavern model assigned",
  "World intent parser model assigned",
  "World narrator model assigned",
  "Cross-Mode model assigned",
  "Quality / summary model assigned",
  "JSON-capable model warning resolved for structured use cases",
  "No real key stored in project",
  "No transient key persisted"
]) {
  requireToken(service, label, `${label} backend checklist item`);
}

const checklistSlice = sourceSlice(providerUi, "function ProviderCompleteSetupChecklist", "function ProviderSetupWizard");
if (checklistSlice.includes("testProjectProviderConnection") || checklistSlice.includes("fetchProjectProviderStatus")) {
  failures.push("Provider checklist UI must not test connections or fetch provider status directly.");
}
if (checklistSlice.includes("Authorization header") || checklistSlice.includes("raw provider response")) {
  failures.push("Provider checklist UI should use safe copy and avoid raw provider-response fields.");
}
if (/<input[^>]+(api_key|secret|transient)/i.test(checklistSlice)) {
  failures.push("Provider checklist UI must not render plaintext secret inputs.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(checklistSlice)) {
  failures.push("Secret-looking sk-* token detected in Provider checklist UI.");
}

if (!service.includes("ProviderSetupChecklistService")) failures.push("Missing ProviderSetupChecklistService backend contract.");
if (!service.includes("validate_provider_model_assignments")) failures.push("Provider checklist must validate model assignment capability warnings.");
if (!service.includes("ProviderConnectionStatusCacheEntry")) failures.push("Provider checklist should read safe connection status cache entries.");
if (service.includes("ProviderGateway") || service.includes("test_connection(") || service.includes("fetch_models(")) {
  failures.push("Provider checklist service must stay read-only and avoid provider network operations.");
}

if (!pkg.scripts?.["check:v37-provider-setup-checklist"]) {
  failures.push("package.json is missing check:v37-provider-setup-checklist.");
}

if (failures.length) {
  console.error("v3.7 provider setup checklist check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 provider setup checklist check passed.");
