import fs from "node:fs";

const app = fs.readFileSync("src/App.tsx", "utf8");
const cache = fs.readFileSync("src/safeApiCache.ts", "utf8");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));

const requiredAppTokens = [
  "SafeApiCacheStatusPanel",
  "writeSafeApiCache(",
  "markSafeApiCacheFailed(",
  "readSafeApiCache<",
  "provider-model-list:",
  "eventlog:",
  "timeline:",
  "quality:world-health:",
  "module-browser:",
  "Manual refresh",
  "stale"
];

const requiredCacheTokens = [
  "const safeApiCacheStore = new Map",
  "transient",
  "api[_-]?key",
  "raw[_-]?provider",
  "raw[_-]?prompt",
  "raw[_-]?output",
  "hidden[_-]?facts",
  "npc[_-]?secrets",
  "raw[_-]?state",
  "mature[_-]?private",
  "writeSafeApiCache",
  "markSafeApiCacheFailed",
  "containsUnsafeCachePayload"
];

function assertToken(source, token, label) {
  if (!source.includes(token)) {
    throw new Error(`Missing ${label}: ${token}`);
  }
}

for (const token of requiredAppTokens) {
  assertToken(app, token, "App safe API cache token");
}

for (const token of requiredCacheTokens) {
  assertToken(cache, token, "safeApiCache token");
}

for (const forbidden of ["localStorage", "sessionStorage", "serviceWorker", "indexedDB"]) {
  if (cache.includes(forbidden)) {
    throw new Error(`safeApiCache must remain in-memory only; found ${forbidden}`);
  }
}

if (!pkg.scripts?.["check:v36-safe-api-cache"]) {
  throw new Error("package.json must expose check:v36-safe-api-cache");
}

console.log("v3.6 safe API cache checks passed.");
