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
  "DraftVersionPanel",
  "WritingSessionDashboard",
  "WorldToNovelImportPanel",
  "DraftSaveStatus",
  "WordCountBadge",
  "buildNovelQualityIssues"
];

const requiredSafetyCopy = [
  ["API key not shown"],
  ["hidden facts"],
  ["raw state_deltas"],
  ["does not directly modify GameState"],
  ["Novel draft / authoring mode", "Novel 草稿 / 创作模式"],
  ["provider status"],
  ["World -> Novel Import UX Pro", "从 World 导入章节草稿", "World-to-Novel 导入"],
  ["No account", "无需账号"],
  ["No cloud sync", "不使用云同步"],
  ["No online marketplace", "无在线市场"]
];

const requiredUsabilityTokens = [
  ["Filter scenes, tags, POV, location"],
  ["missing_chapter_summary"],
  ["Suggested action"],
  ["Draft Version Compare", "草稿版本对比"],
  ["Writing Session Dashboard", "写作会话"],
  ["source event range"]
];

const failures = [];

for (const token of requiredNovelTokens) {
  if (!source.includes(token)) failures.push(`Missing Novel UI Pro token: ${token}`);
}

for (const alternatives of requiredSafetyCopy) {
  if (!alternatives.some((token) => source.includes(token))) failures.push(`Missing Novel safety/local-first copy: ${alternatives.join(" | ")}`);
}

for (const alternatives of requiredUsabilityTokens) {
  if (!alternatives.some((token) => source.includes(token))) failures.push(`Missing v3.1 Novel completion usability token: ${alternatives.join(" | ")}`);
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
