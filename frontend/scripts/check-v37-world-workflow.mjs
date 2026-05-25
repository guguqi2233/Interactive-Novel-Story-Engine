import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const worldUi = readFileSync(resolve(root, "src", "worldUi.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 26000);
}

requireToken(app, "function WorldCompleteWorkflowChecklist", "World Complete Workflow Checklist component");
requireToken(app, "data-v37-world-workflow-check=\"safe-summary\"", "v3.7 World workflow safe summary marker");
requireToken(app, "buildWorldWorkflowChecklistItems", "World workflow checklist builder");
requireToken(app, "Product Readiness Dashboard", "Product dashboard host");
requireToken(app, "World readiness", "World readiness product dashboard item");
requireToken(app, "Missing narrator model warning", "missing narrator model warning copy");
requireToken(app, "Missing intent parser model warning", "missing intent parser model warning copy");
requireToken(app, "Normal play still goes through backend game actions, ActionRegistry, StateDelta, and EventLog", "World boundary copy");
requireToken(app, "never lets the UI directly modify GameState", "direct GameState mutation exclusion copy");
requireToken(app, "never renders hidden facts or raw state_deltas in normal UI", "hidden/raw delta exclusion copy");
requireToken(app, "worldIntentParserAssigned ? \"ready\"", "complete world fixture intent parser ready status path");
requireToken(app, "worldNarratorAssigned ? \"ready\"", "complete world fixture narrator ready status path");
requireToken(app, "providerMissingStatus", "missing provider/model warning status path");

for (const label of [
  "World available",
  "Start game works",
  "Input action available",
  "Suggested actions available",
  "Map/location panel available",
  "NPC panel available",
  "Quest panel available",
  "Inventory/trade available",
  "Advanced modules panels available",
  "Save/load available",
  "Timeline/EventLog available",
  "Visible State Inspector available",
  "World Quality runnable",
  "Provider model assigned for intent parser",
  "Provider model assigned for narrator",
  "normal UI uses visible_state",
  "Debug gated"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const component of [
  "WorldWorkspaceShell",
  "WorldPlayMainView",
  "WorldWorkspaceNavigation",
  "WorldActionInputPanel",
  "LocationCard",
  "NPCRelationshipPanel",
  "QuestJournalPanel",
  "InventoryTradePanel",
  "WorldAdvancedModulePanels",
  "WorldSaveLoadPanel",
  "WorldTimelineEventLogPanel",
  "VisibleStateInspector",
  "WorldQualityPlaytestPanel",
  "WorldPromptProviderPanel",
  "DebugGate"
]) {
  requireToken(app, component, `${component} integration`);
  requireToken(worldUi, component, `${component} component definition`);
}
requireToken(worldUi, "SuggestedActionCard", "SuggestedActionCard component definition");

requireToken(app, "redactReportText(item.safeSummary)", "World checklist safe summary redaction");
requireToken(app, "redactReportText(item.nextAction)", "World checklist next action redaction");
requireToken(worldUi, "Normal World UI uses visible_state only", "visible_state normal boundary copy");
requireToken(worldUi, "UI calls backend APIs and never directly modifies GameState", "backend API action boundary copy");
requireToken(worldUi, "Hidden events are excluded from normal view. Raw state_deltas require DebugGate", "EventLog debug-gated raw delta copy");
requireToken(worldUi, "ENABLE_DEBUG_API required", "DebugGate disabled copy");
requireToken(app, "narration cannot judge world rules", "LLM world authority boundary copy");

const checklist = sourceSlice(app, "function WorldCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "startGame(",
  "submitPlayerInput(",
  "saveGame(",
  "loadGame(",
  "deleteSave(",
  "runWorldHealth(",
  "runPlaytest(",
  "testProjectProviderConnection(",
  "fetchProjectProviderModels(",
  "syncProjectProviderModels(",
  "applyStateDelta",
  "setVisibleState(",
  "setGameState(",
  "fetch("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`World workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("World workflow checklist includes API-key input or transient key terminology outside safe exclusion copy.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${worldUi}`)) {
  failures.push("Secret-looking sk-* token detected in World workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|OnlinePlaySession)/i.test(`${app}\n${worldUi}`)) {
  failures.push("Online/account/cloud/marketplace/online-play enabling entrypoint detected in World workflow frontend source.");
}

if (!pkg.scripts?.["check:v37-world-workflow"]) {
  failures.push("package.json is missing check:v37-world-workflow.");
}

if (failures.length) {
  console.error("v3.7 World workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 World workflow check passed.");
