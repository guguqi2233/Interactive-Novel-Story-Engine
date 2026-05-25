import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const tavernUi = readFileSync(resolve(root, "src", "tavernUi.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 22000);
}

requireToken(app, "function TavernCompleteWorkflowChecklist", "Tavern Complete Workflow Checklist component");
requireToken(app, "data-v37-tavern-workflow-check=\"safe-summary\"", "v3.7 Tavern workflow safe summary marker");
requireToken(app, "buildTavernWorkflowChecklistItems", "Tavern workflow checklist builder");
requireToken(app, "Product Readiness Dashboard", "Product dashboard host");
requireToken(app, "Tavern readiness", "Tavern readiness product dashboard item");
requireToken(app, "Mature module default-off", "mature default-off item");
requireToken(app, "Missing provider warning", "missing Provider warning copy");
requireToken(app, "no online RP", "no online RP boundary copy");
requireToken(app, "no multiplayer session", "no multiplayer boundary copy");
requireToken(app, "no real provider call", "no real provider boundary copy");
requireToken(app, "no direct World GameState mutation", "GameState boundary copy");
requireToken(app, "no NPC secrets or mature memory in normal UI", "NPC secret and mature memory exclusion copy");
requireToken(app, "tavernProviderAssigned ? \"ready\"", "complete Tavern fixture ready status path");
requireToken(app, "projectReady ? \"warning\" : \"missing\"", "missing Provider warning status path");

for (const label of [
  "Character library available",
  "Tavern character editor available",
  "RP/Voice profile available",
  "Single chat available",
  "Multi-NPC scene available",
  "RP memory available",
  "Emotion arc available",
  "Relationship tone available",
  "Scene mood available",
  "Boundary settings available",
  "Mature module default-off",
  "Provider model assigned for Tavern",
  "Tavern -> World proposal available",
  "Tavern -> Novel draft available",
  "RP Safety runnable",
  "Tavern export/backup available",
  "mature/private filtered by default"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const component of [
  "TavernWorkspaceShell",
  "CharacterCardLibrary",
  "TavernCharacterEditor",
  "TavernPromptProviderPanel",
  "SingleCharacterChatPro",
  "MultiNPCScenePro",
  "RPMemoryPanel",
  "EmotionArcPanel",
  "RelationshipTonePanel",
  "SceneMoodPresetPanel",
  "CharacterVoiceLabPanel",
  "BoundaryMatureSettingsPanel",
  "RPSafetyDashboardPanel",
  "TavernCrossModeSafetyPanel"
]) {
  requireToken(app, component, `${component} integration`);
  requireToken(tavernUi, component, `${component} component definition`);
}

requireToken(app, "redactReportText(item.safeSummary)", "Tavern checklist safe summary redaction");
requireToken(app, "redactReportText(item.nextAction)", "Tavern checklist next action redaction");
requireToken(app, "Mature module is default-off", "mature default-off pass copy");
requireToken(app, "unknown age/minor blocks", "mature age policy copy");
requireToken(app, "Normal Tavern UI, prompts, export, backup, and diagnostics filter NPC secrets", "NPC secrets not rendered copy");
requireToken(app, "private persona, mature/private memory", "mature/private filtering copy");
requireToken(tavernUi, "Normal Tavern UI excludes API keys, hidden facts, NPC secrets, mature memory", "normal Tavern UI safe summary copy");
requireToken(tavernUi, "Tavern → World", "Tavern to World proposal UI copy");
requireToken(tavernUi, "Tavern → Novel", "Tavern to Novel draft UI copy");

const checklist = sourceSlice(app, "function TavernCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "createTavernCharacter(",
  "createTavernSession(",
  "sendTavernMessage(",
  "generateMultiNPCNext(",
  "runRPSafetyDashboard(",
  "createTavernSessionExport(",
  "buildTavernApplyPlan(",
  "applyTavernProposal(",
  "testProjectProviderConnection(",
  "fetchProjectProviderModels(",
  "syncProjectProviderModels(",
  "submitPlayerInput(",
  "saveGame(",
  "applyStateDelta",
  "fetch("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Tavern workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("Tavern workflow checklist includes API-key input or transient key terminology outside safe exclusion copy.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${tavernUi}`)) {
  failures.push("Secret-looking sk-* token detected in Tavern workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload|MultiplayerRoom)/i.test(`${app}\n${tavernUi}`)) {
  failures.push("Online/account/cloud/marketplace/multiplayer enabling entrypoint detected in Tavern workflow frontend source.");
}

if (!pkg.scripts?.["check:v37-tavern-workflow"]) {
  failures.push("package.json is missing check:v37-tavern-workflow.");
}

if (failures.length) {
  console.error("v3.7 Tavern workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Tavern workflow check passed.");
