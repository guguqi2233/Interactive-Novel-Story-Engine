import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const desktopUi = readFileSync(resolve(root, "src", "desktopUi.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 36000);
}

requireToken(app, "function LocalPrivacySafetyCompleteReviewPanel", "Local Privacy / Safety Complete Review UI component");
requireToken(app, "data-v37-privacy-safety-review=\"safe-summary\"", "v3.7 privacy safety safe summary marker");
requireToken(app, "buildLocalPrivacySafetyReviewItems", "privacy safety review builder");
requireToken(app, "Local Privacy / Safety Complete Review UI", "privacy safety review title");
requireToken(app, "Product-level local safety review for API keys, transient keys, Provider profiles", "product-level privacy review copy");
requireToken(app, "no API key display", "API key display exclusion copy");
requireToken(app, "no transient key display", "transient key display exclusion copy");
requireToken(app, "no hidden content text", "hidden content display exclusion copy");
requireToken(app, "no NPC secrets", "NPC secret exclusion copy");
requireToken(app, "no raw state_deltas", "raw state delta exclusion copy");
requireToken(app, "no upload", "upload exclusion copy");
requireToken(app, "no auto-fix", "auto-fix exclusion copy");
requireToken(app, "no GameState mutation", "GameState mutation exclusion copy");

for (const label of [
  "API key safety",
  "transient key safety",
  "ProviderProfile safety",
  "visible_state safety",
  "hidden facts safety",
  "NPC secrets safety",
  "debug data gating",
  "mature/private default-off",
  "export filtering",
  "backup filtering",
  "diagnostics filtering",
  "mod permission safety",
  "no account/cloud/marketplace status"
]) {
  requireToken(app, `label: "${label}"`, `${label} privacy/safety item`);
}

for (const token of [
  "SettingsPrivacyPanel",
  "ProviderSettingsPrivacyPanel",
  "Hidden Leak Report UI Pro",
  "Mod Permission Dashboard Pro",
  "备份 / 恢复 / 诊断完整流程检查",
  "Export Complete Workflow Check",
  "Safe Debug Export Wizard",
  "ProviderProfile limited to api_key_env or secret_ref",
  "One-time provider test/fetch keys are accepted only for that local request",
  "raw state_deltas and raw debug details are unavailable in normal UI",
  "Mature Module and mature/private export remain opt-in/default-off",
  "packages are not executed and arbitrary code plugins remain disallowed",
  "no account system, no cloud sync, no online marketplace"
]) {
  requireToken(app, token, `${token} privacy/safety integration`);
}

for (const token of [
  "设置 / 隐私 / 模型服务",
  "api_key_env",
  "secret_ref",
  "Authorization header",
  "明文 API key",
  "raw provider error"
]) {
  requireToken(providerUi, token, `${token} provider privacy UI integration`);
}

for (const token of [
  "Local Settings / Privacy",
  "Privacy",
  "Local-first privacy notice",
  "no upload",
  "no cloud sync",
  "no accounts",
  "no online project service"
]) {
  requireToken(desktopUi, token, `${token} desktop privacy integration`);
}

requireToken(app, "configErrors.length ? \"warning\" : \"ready\"", "missing safety config warning path");
requireToken(app, "backupFilteringSafe", "backup filtering safety path");
requireToken(app, "diagnosticsFilteringSafe", "diagnostics filtering safety path");
requireToken(app, "containsSensitiveLogMarker(`${cacheStatus.summary} ${cacheStatus.safeError ?? \"\"}`)", "provider/cache secret marker guard");

const checklist = sourceSlice(app, "function LocalPrivacySafetyCompleteReviewPanel", "function buildProductReadinessItems");
for (const forbidden of [
  "fetch(",
  "requestJson(",
  "setGameState(",
  "setVisibleState(",
  "submitPlayerInput(",
  "applyStateDelta",
  "createLocalBackup(",
  "createDiagnosticsBundle(",
  "restoreApply(",
  "exportNovelManuscript(",
  "createTavernSessionExport(",
  "testProjectProviderConnection(",
  "fetchProjectProviderModels(",
  "saveProjectProviderProfile("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Privacy / Safety review must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist)) {
  failures.push("Privacy / Safety review includes API-key input.");
}

if (/JSON\.stringify\([^)]*(env|prompt|state_delta|secret|hidden|npc_knowledge)/i.test(checklist) || /<pre>/i.test(checklist)) {
  failures.push("Privacy / Safety review appears to render raw sensitive/debug payloads.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${providerUi}\n${desktopUi}`)) {
  failures.push("Secret-looking sk-* token detected in privacy/safety frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|CloudBackup|OnlineDiagnosticsUpload)/i.test(`${app}\n${providerUi}\n${desktopUi}`)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected.");
}

if (!pkg.scripts?.["check:v37-privacy-safety-review"]) {
  failures.push("package.json is missing check:v37-privacy-safety-review.");
}

if (failures.length) {
  console.error("v3.7 Privacy / Safety review check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Privacy / Safety review check passed.");
