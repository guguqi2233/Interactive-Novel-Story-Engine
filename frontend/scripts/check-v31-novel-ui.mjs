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

const requiredNovelTokens = [
  "NovelWorkspaceShell",
  "OutlineTreePro",
  "ChapterEditorPro",
  "SceneCardsBoard",
  "ManuscriptDashboard",
  "CharacterArcPanel",
  "PlotForeshadowingBoard",
  "TimelineLinkPanel",
  "WorldBibleSidebar",
  "NovelExportWizard",
  "NovelQualityDashboard",
  "NovelPromptProviderPanel",
  "DraftSaveStatus",
  "WordCountBadge"
];

const requiredSafetyCopy = [
  "API key not shown",
  "hidden facts",
  "raw state_deltas",
  "does not directly modify GameState",
  "No account",
  "No cloud sync",
  "No online marketplace"
];

const failures = [];

for (const token of requiredNovelTokens) {
  if (!source.includes(token)) failures.push(`Missing Novel UI Pro token: ${token}`);
}

for (const token of requiredSafetyCopy) {
  if (!source.includes(token)) failures.push(`Missing Novel safety/local-first copy: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(source) || /api_key:\s*["'][^"']+/i.test(source)) {
  failures.push("Plaintext api_key input or literal detected in frontend source.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(source + scripts)) {
  failures.push("Secret-looking sk-* token detected in frontend files.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online Publishing|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online Publishing|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(source)) failures.push("Account/cloud/online publishing/marketplace appears as a primary UI entry.");
}

if (!/"check:v31-novel-ui"/.test(pkg)) failures.push("package.json is missing check:v31-novel-ui.");

if (failures.length) {
  console.error("v3.1 Novel UI regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.1 Novel UI regression check passed.");
