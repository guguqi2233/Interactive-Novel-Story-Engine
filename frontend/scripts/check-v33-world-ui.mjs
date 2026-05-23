import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));

function readTree(dir) {
  let text = "";
  for (const entry of readdirSync(dir)) {
    const full = resolve(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) text += readTree(full);
    else if (/\.(tsx?|mjs)$/.test(entry)) text += `\n/* ${full} */\n${readFileSync(full, "utf8")}`;
  }
  return text;
}

const source = readTree(resolve(root, "src"));
const scripts = readTree(resolve(root, "scripts"));
const pkg = readFileSync(resolve(root, "package.json"), "utf8");

const requiredWorldTokens = [
  "WorldWorkspaceShell",
  "WorldPlayMainView",
  "MapLocationPanel",
  "NPCRelationshipPanel",
  "QuestJournalPanel",
  "InventoryTradePanel",
  "TacticalCombatPanel",
  "EconomyDashboardPanel",
  "FactionWarDashboardPanel",
  "DeductionBoardPanel",
  "SurvivalTravelPanel",
  "WorldAdvancedModulePanels",
  "WorldTimelineEventLogPanel",
  "VisibleStateInspector",
  "WorldSaveLoadPanel",
  "WorldQualityPlaytestPanel",
  "WorldPromptProviderPanel",
  "WorldActionInputPanel",
  "DebugGate"
];

const requiredSafetyCopy = [
  "visible_state",
  "API key",
  "hidden facts",
  "NPC secrets",
  "raw state_deltas",
  "ENABLE_DEBUG_API",
  "does not directly modify GameState",
  "No account",
  "No cloud sync",
  "No online marketplace",
  "No online play"
];

const failures = [];

for (const token of requiredWorldTokens) {
  if (!source.includes(token)) failures.push(`Missing World UI Pro token: ${token}`);
}

for (const token of requiredSafetyCopy) {
  if (!source.includes(token)) failures.push(`Missing World safety/local-first copy: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(source) || /api_key:\s*["'][^"']+/i.test(source)) {
  failures.push("Plaintext api_key input or literal detected in frontend source.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(source + scripts)) {
  failures.push("Secret-looking sk-* token detected in frontend files.");
}

if (/JSON\.stringify\(event\.state_deltas/.test(source) && !source.includes("DebugGate")) {
  failures.push("Raw state_deltas rendering exists without DebugGate token.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Play|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Play|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(source)) failures.push("Account/cloud/online play/marketplace appears as a primary UI entry.");
}

if (!/"check:v33-world-ui"/.test(pkg)) failures.push("package.json is missing check:v33-world-ui.");

if (failures.length) {
  console.error("v3.3 World UI regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.3 World UI regression check passed.");
