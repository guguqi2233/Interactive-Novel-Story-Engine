import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const css = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

for (const [token, label] of [
  ["function LoadingSkeletonPanel", "shared skeleton component"],
  ["function ProgressiveLoadNote", "progressive refresh note"],
  ["data-v36-loading-skeleton=\"safe\"", "safe skeleton marker"],
  ["data-v36-progressive-rendering=\"summary-first\"", "summary-first marker"],
  ["data-v36-progressive-rendering=\"summary-before-list\"", "summary-before-list marker"],
  ["Quality Dashboard staged loading", "quality dashboard staged loading"],
  ["Provider model metadata loading", "provider model list loading"],
  ["EventLog loading", "EventLog loading state"],
  ["Timeline Replay loading", "Timeline replay loading state"],
  ["Module Browser package list loading", "module browser loading state"],
  ["Backup preview staged loading", "backup staged loading state"],
  ["Diagnostics preview staged loading", "diagnostics staged loading state"],
  ["Novel dashboard loading", "Novel dashboard loading state"],
  ["Tavern dashboard loading", "Tavern dashboard loading state"],
  ["World dashboard loading", "World dashboard loading state"],
  ["hidden facts", "route fallback privacy copy"],
  ["raw StateDelta payloads stay out of normal view", "StateDelta safe loading copy"]
]) {
  requireToken(app, token, label);
}

for (const [token, label] of [
  [".progressive-loading-skeleton", "skeleton style"],
  [".progressive-load-note", "progressive note style"],
  [".skeleton-row", "skeleton rows"],
  ["@keyframes skeleton-safe-pulse", "safe skeleton animation"],
  [".reduced-motion-root .skeleton-line", "reduced motion skeleton rule"]
]) {
  requireToken(css, token, label);
}

requireToken(pkg, "\"check:v36-loading-progressive\"", "package script");

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("v3.6 Loading Skeleton / Progressive Rendering check passed.");
