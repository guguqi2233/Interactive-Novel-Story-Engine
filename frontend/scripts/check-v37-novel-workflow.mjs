import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const novelUi = readFileSync(resolve(root, "src", "novelUi.tsx"), "utf8");
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
  return source.slice(start, end > start ? end : start + 18000);
}

requireToken(app, "function NovelCompleteWorkflowChecklist", "Novel Complete Workflow Checklist component");
requireToken(app, "data-v37-novel-workflow-check=\"safe-summary\"", "v3.7 Novel workflow safe summary marker");
requireToken(app, "buildNovelWorkflowChecklistItems", "Novel workflow checklist builder");
requireToken(app, "Product Readiness Dashboard", "Product dashboard host");
requireToken(app, "Novel readiness", "Novel readiness product dashboard item");
requireToken(app, "No online writing requirement", "local-only Novel workflow item");
requireToken(app, "Export filters secrets / hidden / mature/private", "safe export filter item");
requireToken(app, "Missing provider warning", "missing Provider warning copy");
requireToken(app, "no real provider call", "no real provider boundary copy");
requireToken(app, "no World GameState mutation", "GameState boundary copy");
requireToken(app, "no hidden facts or raw state_deltas", "normal UI hidden/raw delta exclusion copy");
requireToken(app, "novelProviderAssigned ? \"ready\"", "complete Novel fixture ready status path");
requireToken(app, "projectReady ? \"warning\" : \"missing\"", "missing Provider warning status path");

for (const label of [
  "Manuscript exists or can be created",
  "Outline available",
  "Chapter editor available",
  "Scene cards available",
  "Character arcs available",
  "Plot/Foreshadowing available",
  "World Bible sidebar available",
  "Timeline links available",
  "Provider model assigned for novel",
  "World -> Novel import available",
  "Novel export available",
  "Novel quality runnable",
  "No online writing requirement",
  "Export filters secrets / hidden / mature/private"
]) {
  requireToken(app, `label: "${label}"`, `${label} checklist item`);
}

for (const component of [
  "NovelWorkspaceShell",
  "ManuscriptDashboard",
  "OutlineTreePro",
  "ChapterEditorPro",
  "SceneCardsBoard",
  "CharacterArcPanel",
  "PlotForeshadowingBoard",
  "WorldBibleSidebar",
  "TimelineLinkPanel",
  "NovelPromptProviderPanel",
  "WorldToNovelImportPanel",
  "NovelExportWizard",
  "NovelQualityDashboard"
]) {
  requireToken(app, component, `${component} integration`);
  requireToken(novelUi, component, `${component} component definition`);
}

requireToken(app, "redactReportText(item.safeSummary)", "Novel checklist safe summary redaction");
requireToken(app, "redactReportText(item.nextAction)", "Novel checklist next action redaction");
requireToken(app, "Default Novel export filters API keys", "export filter warning pass");
requireToken(app, "hidden refs, mature/private content", "hidden/private export filter copy");
requireToken(app, "World Bible sidebar shows safe references; hidden facts and NPC secrets are not rendered.", "hidden facts not rendered copy");

const checklist = sourceSlice(app, "function NovelCompleteWorkflowChecklist", "function buildProductReadinessItems");
for (const forbidden of [
  "previewWorldToNovel(",
  "createNovelManuscript(",
  "createNovelChapter(",
  "createNovelScene(",
  "exportNovelManuscript(",
  "testProjectProviderConnection(",
  "fetchProjectProviderModels(",
  "syncProjectProviderModels(",
  "submitPlayerInput(",
  "saveGame(",
  "applyStateDelta",
  "fetch("
]) {
  if (checklist.includes(forbidden)) {
    failures.push(`Novel workflow checklist must remain read-only but includes ${forbidden}.`);
  }
}

if (/<input[^>]+api[_-]?key/i.test(checklist) || /transient_api_key/i.test(checklist)) {
  failures.push("Novel workflow checklist includes API-key input or transient key terminology outside safe exclusion copy.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(`${app}\n${novelUi}`)) {
  failures.push("Secret-looking sk-* token detected in Novel workflow frontend source.");
}

if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i.test(`${app}\n${novelUi}`)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected in Novel workflow frontend source.");
}

if (!pkg.scripts?.["check:v37-novel-workflow"]) {
  failures.push("package.json is missing check:v37-novel-workflow.");
}

if (failures.length) {
  console.error("v3.7 Novel workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Novel workflow check passed.");
