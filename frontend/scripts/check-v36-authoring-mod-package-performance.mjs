import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

function requireToken(token, label) {
  if (!appSource.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const [token, label] of [
  ["AUTHORING_LARGE_PACKAGE_PAGE_SIZES", "shared authoring package page sizes"],
  ["data-windowed-authoring-package-list", "windowed authoring package list marker"],
  ["data-windowed-module-browser", "windowed Module Browser marker"],
  ["data-windowed-compatibility-matrix", "windowed compatibility matrix marker"],
  ["data-collapsed-compatibility-matrix", "collapsed compatibility matrix summary marker"],
  ["data-grouped-permission-risk", "permission risk grouping marker"],
  ["data-segmented-import-export-preview", "segmented import/export preview marker"],
  ["data-grouped-authoring-validation", "grouped authoring validation marker"],
  ["data-windowed-authoring-validation-issues", "windowed authoring validation issue marker"],
  ["safePreviewItems", "safe preview truncation helper"],
  ["No online marketplace", "local-only marketplace boundary copy"],
  ["no remote download", "remote download boundary copy"],
  ["no package execution", "package execution boundary copy"],
  ["No arbitrary code execution", "arbitrary code boundary copy"]
]) {
  requireToken(token, label);
}

for (const stalePattern of [
  "matrix.entries.map((entry) =>",
  "modulePermissionSummaries.map((item) =>",
  "moduleDetail.dependencies.join(\", \")",
  "moduleDetail.conflicts.join(\", \")",
  "JSON.stringify(report.normal_manifest"
]) {
  if (appSource.includes(stalePattern)) failures.push(`Found stale large Authoring/Mod render pattern: ${stalePattern}`);
}

if (/sk-[A-Za-z0-9_-]{20,}/.test(appSource)) {
  failures.push("Secret-looking token detected in App.tsx.");
}

if (/online marketplace/i.test(appSource) && !/No online marketplace|no online marketplace/i.test(appSource)) {
  failures.push("Online marketplace wording appears without a local-only denial.");
}

if (!/"check:v36-authoring-mod-package-performance"/.test(pkg)) {
  failures.push("package.json is missing check:v36-authoring-mod-package-performance.");
}

if (failures.length) {
  console.error("v3.6 Authoring/Mod package performance check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Authoring/Mod package performance check passed.");
