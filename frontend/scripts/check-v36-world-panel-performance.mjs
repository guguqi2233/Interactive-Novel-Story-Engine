import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const worldSource = readFileSync(resolve(root, "src", "worldUi.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

function requireToken(token, label) {
  if (!worldSource.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const [token, label] of [
  ["useDebouncedValue", "debounced safe search"],
  ["safeSearchMatches", "safe search matching"],
  ["data-windowed-world-npcs", "windowed NPC list marker"],
  ["data-windowed-world-quests", "windowed quest list marker"],
  ["data-windowed-world-inventory", "windowed inventory list marker"],
  ["data-collapsible-visible-state-inspector", "collapsible visible state inspector marker"],
  ["PaginationControls", "shared World panel pagination"],
  ["NPC secrets, NPC hidden knowledge, hidden relationships, and debug memory are not displayed.", "NPC privacy boundary copy"],
  ["Hidden objectives, hidden truth, and debug quest state are excluded from normal view.", "quest privacy boundary copy"],
  ["Hidden item properties and debug economy data are excluded.", "item privacy boundary copy"],
  ["raw state_deltas", "raw StateDelta exclusion copy"]
]) {
  requireToken(token, label);
}

for (const stalePattern of [
  "npcs.length ? npcs.map((npc) => <NPCSafeCard",
  "quests.length ? quests.map((quest) => <QuestCard",
  "inventory.length ? inventory.map((item) => <InventoryItemCard",
  "visibleObjects.map((item) => item.id).join"
]) {
  if (worldSource.includes(stalePattern)) failures.push(`Found stale full World panel render pattern: ${stalePattern}`);
}

if (/known_facts\.map\(\(fact\).*fact\.text/s.test(worldSource)) {
  failures.push("Visible State Inspector appears to render known fact text instead of safe ids.");
}

if (/state_deltas\.map|JSON\.stringify\(.*state_deltas/s.test(worldSource) && !worldSource.includes("DebugGate")) {
  failures.push("World UI appears to render raw state_deltas without DebugGate.");
}

if (/sk-[A-Za-z0-9_-]{20,}/.test(worldSource)) {
  failures.push("Secret-looking token detected in worldUi.tsx.");
}

if (!/"check:v36-world-panel-performance"/.test(pkg)) {
  failures.push("package.json is missing check:v36-world-panel-performance.");
}

if (failures.length) {
  console.error("v3.6 World panel performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 World panel performance check passed.");
