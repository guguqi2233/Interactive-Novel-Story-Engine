import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const novelSource = readFileSync(resolve(root, "src", "novelUi.tsx"), "utf8");
const tavernSource = readFileSync(resolve(root, "src", "tavernUi.tsx"), "utf8");
const filterUtilsSource = readFileSync(resolve(root, "src", "filterUtils.ts"), "utf8");
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const token of ["useDebouncedValue", "buildSafeSearchIndex", "safeSearchMatches", "SECRET_LIKE_PATTERNS"]) {
  requireToken(filterUtilsSource, token, "shared safe filter utility token");
}

for (const token of [
  "debouncedModelSearch",
  "modelSearchIndexByRowId",
  "safeSearchMatches(modelSearchIndexByRowId",
  "qualityIssueSearchIndexById",
  "hiddenLeakSearchIndexById",
  "debouncedPathSearch",
  "stateDeltaSearchIndexByRow",
  "debouncedModuleSearchQuery",
  "moduleSearchIndexById",
  "data-windowed-module-browser"
]) {
  requireToken(appSource, token, "App search/filter performance token");
}

for (const token of [
  "debouncedFilter",
  "sceneSearchIndexById",
  "safeSearchMatches(sceneSearchIndexById",
  "draftValue",
  "debouncedValue",
  "debouncedTag"
]) {
  requireToken(novelSource, token, "Novel search/filter performance token");
}

for (const token of [
  "debouncedQuery",
  "characterSearchIndexById",
  "debouncedMessageSearch",
  "messageSearchIndexById",
  "visibleMessages",
  "debouncedMemorySearch",
  "memorySearchIndexByKey"
]) {
  requireToken(tavernSource, token, "Tavern search/filter performance token");
}

for (const stalePattern of [
  "const query = modelSearch.trim().toLowerCase()",
  "const query = issueSearch.trim().toLowerCase()",
  "pathSearch.toLowerCase()",
  "moduleSearchQuery.trim().toLowerCase()"
]) {
  if (appSource.includes(stalePattern)) failures.push(`Found stale synchronous search pattern in App.tsx: ${stalePattern}`);
}

for (const [label, source] of [
  ["App.tsx", appSource],
  ["novelUi.tsx", novelSource],
  ["tavernUi.tsx", tavernSource],
  ["filterUtils.ts", filterUtilsSource]
]) {
  if (/sk-[A-Za-z0-9_-]{20,}/.test(source)) {
    failures.push(`Secret-looking token detected in ${label}.`);
  }
}

if (failures.length) {
  console.error("v3.6 search/filter performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 search/filter performance check passed.");
