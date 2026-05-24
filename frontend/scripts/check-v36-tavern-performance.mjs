import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const tavernSource = readFileSync(resolve(root, "src", "tavernUi.tsx"), "utf8");
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const token of [
  "export function TavernSessionListPro",
  "data-windowed-tavern-sessions",
  "export function TavernMessageListPro",
  "data-windowed-tavern-message-list",
  "data-windowed-tavern-messages",
  "jumpToLatestMessage",
  "data-windowed-multi-npc-scenes",
  "Jump to latest",
  "data-windowed-rp-memory",
  "debouncedMemorySearch",
  "debouncedSceneSearch",
  "safeSearchMatches"
]) {
  requireToken(tavernSource, token, "Tavern performance token");
}

for (const token of [
  "TavernSessionListPro",
  "TavernMessageListPro",
  "selectTavernSession"
]) {
  requireToken(appSource, token, "App Tavern performance integration token");
}

for (const stalePattern of [
  "items={tavernSessions.map",
  "items={tavernMessages.map",
  "items={multiNPCScenes.map"
]) {
  if (appSource.includes(stalePattern)) failures.push(`Found stale full Tavern list render pattern: ${stalePattern}`);
}

if (/mature_only.*visible.*true/i.test(tavernSource)) {
  failures.push("Tavern UI appears to force mature_only visibility on.");
}

for (const [label, source] of [
  ["App.tsx", appSource],
  ["tavernUi.tsx", tavernSource]
]) {
  if (/sk-[A-Za-z0-9_-]{20,}/.test(source)) {
    failures.push(`Secret-looking token detected in ${label}.`);
  }
}

if (failures.length) {
  console.error("v3.6 Tavern performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Tavern performance check passed.");
