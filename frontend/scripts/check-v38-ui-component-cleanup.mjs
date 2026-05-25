import { readFileSync } from "node:fs";

const app = readFileSync(new URL("../src/App.tsx", import.meta.url), "utf8");
const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8"));
const failures = [];

function requireToken(token, label) {
  if (!app.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

for (const [token, label] of [
  ["function MainModeCard", "MainModeCard extraction"],
  ["function ProductNextStepCard", "ProductNextStepCard extraction"],
  ["function BackendUnavailableState", "BackendUnavailableState component"],
  ["function ProviderMissingState", "ProviderMissingState extraction"],
  ["function EmptyState", "Chinese empty state base component"],
  ["function LocalSafetySummary", "LocalSafetySummary extraction"],
  ["function ProductCTAGroup", "ProductCTAGroup extraction"],
  ["function DemoProjectCard", "DemoProjectCard extraction"],
  ["function InlineGuideCard", "ProductHelpHint/InlineGuide extraction"],
  ["<MainModeCard", "Home uses MainModeCard"],
  ["<ProductNextStepCard", "Home uses ProductNextStepCard"],
  ["<ProviderMissingState", "Home uses ProviderMissingState"],
  ["<LocalSafetySummary", "Home uses LocalSafetySummary"],
  ["<ProductCTAGroup", "Home uses ProductCTAGroup"],
  ["<DemoProjectCard", "Home uses DemoProjectCard"]
]) {
  requireToken(token, label);
}

const homeSlice = app.slice(app.indexOf("function ChinesePlayableHomePanel"), app.indexOf("function ProjectHomeRedesignPanel"));
const repeatedArticleCount = (homeSlice.match(/cn-mode-entry-featured/g) ?? []).length;
if (repeatedArticleCount > 1) {
  failures.push(`Home still repeats featured main mode markup ${repeatedArticleCount} times instead of using MainModeCard.`);
}

for (const forbidden of [/sk-[A-Za-z0-9_-]{12,}/, /Authorization\s*:/i, /raw_state_deltas.*normal/i]) {
  if (forbidden.test(homeSlice)) failures.push(`Home cleanup slice contains forbidden pattern: ${forbidden}`);
}

if (!pkg.scripts?.["check:v38-ui-component-cleanup"]) {
  failures.push("package.json is missing check:v38-ui-component-cleanup.");
}

if (failures.length) {
  console.error("v3.8 UI component cleanup check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 UI component cleanup check passed.");
