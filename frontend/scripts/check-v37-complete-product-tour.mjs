import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 18000);
}

requireToken(app, "const COMPLETE_PRODUCT_TOUR_STEPS", "complete product tour step list");
requireToken(app, "function FirstRunOnboardingFlow", "first-run tour component");
requireToken(app, "First-Run Complete Product Tour", "tour title");
requireToken(app, "Open Product Tour", "reopen product tour button");
requireToken(app, "function reopenFirstRunOnboarding", "tour reopen handler");
requireToken(app, "removeItem(FIRST_RUN_ONBOARDING_KEY)", "local skip/completion reset");
requireToken(app, "Skip onboarding", "skip button");
requireToken(app, "Finish", "finish button");
requireToken(app, "Tour state is stored locally as completed/skipped only", "local-only tour storage copy");

for (const title of [
  "Welcome: local-first",
  "Create/Open Project",
  "Configure Provider",
  "Test Connection / Fetch Models",
  "Assign Models by Mode",
  "Open Novel Studio",
  "Open Tavern Studio",
  "Open World Studio",
  "Cross-Mode overview",
  "Authoring / Mod overview",
  "Quality / Debug / Replay overview",
  "Backup / Restore / Diagnostics overview",
  "Privacy / secrets overview"
]) {
  requireToken(app, `title: "${title}"`, `${title} tour step`);
}

for (const copy of [
  "No account",
  "no cloud sync",
  "no online marketplace",
  "remote package download",
  "Provider setup can be skipped",
  "The tour never asks for a plaintext key",
  "this tour never calls a real provider",
  "Onboarding never modifies GameState",
  "telemetry"
]) {
  requireToken(app, copy, `${copy} safety copy`);
}

const tour = sourceSlice(app, "function FirstRunOnboardingFlow", "function ModeLandingPage");
if (tour.includes("fetch(") || tour.includes("requestJson") || tour.includes("testProjectProviderConnection")) {
  failures.push("First-run product tour must not call network/provider APIs.");
}
if (tour.includes("submitPlayerInput") || tour.includes("saveGame(") || tour.includes("applySaveMigration")) {
  failures.push("First-run product tour must not modify GameState.");
}
if (tour.includes("api_key") && !tour.includes("api_key_env")) {
  failures.push("Tour should mention api_key_env/secret_ref boundaries, not plaintext api_key fields.");
}

requireToken(styles, ".product-tour-steps", "tour step list styles");
requireToken(styles, ".product-tour-step-panel", "tour step panel styles");
requireToken(styles, ".secondary-action", "reopen tour button styles");

if (!pkg.scripts?.["check:v37-complete-product-tour"]) {
  failures.push("package.json is missing check:v37-complete-product-tour.");
}

const sourceBundle = `${app}\n${styles}`;
if (/sk-[A-Za-z0-9_-]{12,}/.test(sourceBundle)) {
  failures.push("Secret-looking sk-* token detected in v3.7 tour source.");
}
if (/<input[^>]+name=["']api_key["']/i.test(sourceBundle)) {
  failures.push("Plaintext api_key input detected in frontend UI.");
}
if (/create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i.test(sourceBundle)) {
  failures.push("Online/account/cloud/marketplace enabling entrypoint detected.");
}

if (failures.length) {
  console.error("v3.7 complete product tour check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 complete product tour check passed.");
