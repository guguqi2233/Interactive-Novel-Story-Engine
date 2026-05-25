import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
const providerUi = readFileSync(new URL("../src/providerUi.tsx", import.meta.url), "utf8");
const styles = readFileSync(new URL("../src/styles.css", import.meta.url), "utf8");
const source = `${app}\n${providerUi}\n${styles}`;

const requiredTokens = [
  "function InlineGuideCard",
  "inline-guide-card",
  "id=\"product-guide\"",
  "了解更多",
  "v38-inline-guide-home",
  "v38-inline-guide-provider",
  "v38-inline-guide-model-assignment",
  "v38-inline-guide-novel",
  "v38-inline-guide-tavern",
  "v38-inline-guide-world",
  "v38-inline-guide-backup",
  "v38-inline-guide-diagnostics",
  "v38-inline-guide-debug",
  "v38-inline-guide-authoring",
  "本地优先",
  "不会上传",
  "DebugGate",
  "API Key"
];

const missing = requiredTokens.filter((token) => !source.includes(token));
if (missing.length > 0) {
  console.error("v3.8 inline guide check failed. Missing tokens:");
  for (const token of missing) {
    console.error(`- ${token}`);
  }
  process.exit(1);
}

const inlineGuideSlices = [...source.matchAll(/<InlineGuideCard[\s\S]*?\/>/g)].map((match) => match[0]);
if (inlineGuideSlices.length < 9) {
  console.error(`Expected at least 9 inline guide cards, found ${inlineGuideSlices.length}.`);
  process.exit(1);
}

const forbiddenPatterns = [
  /sk-[A-Za-z0-9_-]{12,}/,
  /Authorization\s*:/i,
  /http:\/\/|https:\/\//i,
  /telemetry/i,
  /cloud sync/i,
  /online marketplace/i
];

for (const slice of inlineGuideSlices) {
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(slice)) {
      console.error(`Inline guide contains forbidden content matching ${pattern}.`);
      process.exit(1);
    }
  }
}

const debugGuideIndex = app.indexOf("v38-inline-guide-debug");
const debugPanelIndex = app.indexOf("id=\"debug-panel\"");
if (debugGuideIndex < debugPanelIndex) {
  console.error("Debug inline guide must remain inside the advanced debug panel.");
  process.exit(1);
}

console.log("v3.8 inline guide check passed.");
