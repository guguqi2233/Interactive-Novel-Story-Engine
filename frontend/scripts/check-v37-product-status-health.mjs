import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  const options = Array.isArray(token) ? token : [token];
  if (!options.some((option) => source.includes(option))) {
    failures.push(`Missing ${label}: ${options.join(" or ")}`);
  }
}

function sourceSlice(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 24000);
}

requireToken(app, "function LocalStatusBar", "LocalStatusBar component");
requireToken(app, "Backend health:", "backend health status bar item");
requireToken(app, "Project loaded", "project loaded status bar item");
requireToken(app, "Provider status:", "provider status bar item");
requireToken(app, "Model assignment:", "model assignment status bar item");
requireToken(app, "Quality status:", "quality status bar item");
requireToken(app, "Debug status:", "debug status bar item");
requireToken(app, "Backup / diagnostics:", "backup diagnostics status bar item");

requireToken(app, ["Overall Health Summary", "整体健康摘要"], "Product Home health summary");
requireToken(app, "Product health safe summary", "health summary aria label");
requireToken(app, ["Safe health summary for backend, project, Provider, model assignment, Quality, Debug, Backup, and Diagnostics.", "安全健康摘要覆盖后端、项目、Provider、模型分配、Quality、Debug、备份和诊断"], "safe health summary copy");
requireToken(app, "Missing provider warning", "missing provider warning copy");
requireToken(app, "unavailable", "backend unavailable state copy");
requireToken(app, ["Raw env, API keys, sensitive local paths, hidden facts, and raw debug data are not shown.", "不显示 raw env、API Key、敏感路径、hidden facts 或 raw debug data"], "safe health exclusion copy");

const localStatusBar = sourceSlice(app, "function LocalStatusBar", "function SafePathSummary");
for (const forbidden of [
  "fetchProjectProviderStatus",
  "testProjectProviderConnection",
  "runDesktopHealthCheck",
  "setGameState",
  "applyStateDelta",
  "transient_api_key",
  "Authorization",
  "raw_state_delta",
  "hidden fact text"
]) {
  if (localStatusBar.includes(forbidden)) {
    failures.push(`LocalStatusBar includes forbidden active call or sensitive token: ${forbidden}`);
  }
}

const productHome = sourceSlice(app, "function ProjectHomeRedesignPanel", "function LocalHelpOnboardingPanel");
for (const token of [
  "Backend health",
  "Project loaded",
  "Provider status",
  "Model assignment status",
  "Quality status",
  "Debug status",
  "Backup / diagnostics status"
]) {
  requireToken(productHome, token, `${token} Product Home health item`);
}

for (const forbidden of [
  "testProjectProviderConnection",
  "fetchProjectProviderStatus",
  "createDiagnosticsBundle(",
  "createBackup(",
  "setGameState",
  "applyStateDelta",
  "sk-"
]) {
  if (productHome.includes(forbidden)) {
    failures.push(`Product Home health summary includes forbidden call or secret-like token: ${forbidden}`);
  }
}

requireToken(styles, ".product-health-summary", "product health summary style");

if (!pkg.scripts?.["check:v37-product-status-health"]) {
  failures.push("package.json is missing check:v37-product-status-health.");
}

if (failures.length) {
  console.error("v3.7 product status/health check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 product status/health check passed.");
