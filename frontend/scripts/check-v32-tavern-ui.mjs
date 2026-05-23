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

const requiredTavernTokens = [
  "TavernWorkspaceShell",
  "TavernCharacterCard",
  "TavernSessionCard",
  "RPMessageBubble",
  "Character Card Library",
  "Tavern Character Editor",
  "Single Character Chat Pro",
  "Multi-NPC Scene Pro",
  "RP Memory Panel",
  "Emotion Arc Panel",
  "Relationship Tone Panel",
  "Scene Mood UI",
  "Character Voice Lab UI",
  "Boundary / Mature Settings UI",
  "RP Safety Dashboard",
  "Tavern Prompt / Provider"
];

const requiredSafetyCopy = [
  "API key not shown",
  "hidden facts",
  "NPC secrets",
  "mature memory",
  "Mature Module is disabled by default",
  "does not modify World GameState",
  "No account",
  "No cloud sync",
  "No online marketplace"
];

const failures = [];

for (const token of requiredTavernTokens) {
  if (!source.includes(token)) failures.push(`Missing Tavern UI Pro token: ${token}`);
}

for (const token of requiredSafetyCopy) {
  if (!source.includes(token)) failures.push(`Missing Tavern safety/local-first copy: ${token}`);
}

if (/<input[^>]+name=["']api_key["']/i.test(source) || /api_key:\s*["'][^"']+/i.test(source)) {
  failures.push("Plaintext api_key input or literal detected in frontend source.");
}

if (/sk-[A-Za-z0-9_-]{12,}/.test(source + scripts)) {
  failures.push("Secret-looking sk-* token detected in frontend files.");
}

const forbiddenPrimaryEntrypoints = [
  /<button[^>]*>\s*(Account|Cloud Sync|Online RP|Online Publishing|Online Marketplace)\s*<\/button>/i,
  /<h[1-6][^>]*>\s*(Account|Cloud Sync|Online RP|Online Publishing|Online Marketplace)\s*<\/h[1-6]>/i
];

for (const pattern of forbiddenPrimaryEntrypoints) {
  if (pattern.test(source)) failures.push("Account/cloud/online RP/publishing/marketplace appears as a primary UI entry.");
}

if (!/"check:v32-tavern-ui"/.test(pkg)) failures.push("package.json is missing check:v32-tavern-ui.");

if (failures.length) {
  console.error("v3.2 Tavern UI regression check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.2 Tavern UI regression check passed.");
