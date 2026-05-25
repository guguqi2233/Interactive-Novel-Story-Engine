import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const read = (...parts) => readFileSync(resolve(root, ...parts), "utf8");
const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function forbidPattern(source, pattern, label) {
  if (pattern.test(source)) failures.push(`Forbidden ${label}: ${pattern}`);
}

function runCheck(scriptName) {
  const scriptPath = resolve(root, "scripts", scriptName);
  if (!existsSync(scriptPath)) {
    failures.push(`Missing delegated check script: ${scriptName}`);
    return;
  }
  try {
    execFileSync(process.execPath, [scriptPath], {
      cwd: root,
      stdio: "inherit",
      env: {
        ...process.env,
        LLM_PROVIDER: "mock",
        PROVIDER_TEST_MODE: "fake"
      }
    });
  } catch {
    failures.push(`Delegated check failed: ${scriptName}`);
  }
}

const app = read("src", "App.tsx");
const api = read("src", "api.ts");
const providerUi = read("src", "providerUi.tsx");
const desktopUi = read("src", "desktopUi.tsx");
const pkg = JSON.parse(read("package.json"));
const combined = `${app}\n${api}\n${providerUi}\n${desktopUi}`;

runCheck("check-v37-product-cn.mjs");
runCheck("check-v38-product-ux.mjs");
runCheck("check-v38-integration-regression.mjs");

for (const token of [
  "data-testid=\"v37-cn-playable-home\"",
  "写小说",
  "角色 RP",
  "大世界游玩",
  "打开项目",
  "创建项目",
  "配置模型服务",
  "data-testid=\"v37-home-advanced-tools\"",
  "data-testid=\"v37-advanced-tools-nav\"",
  "调试 / 回放",
  "备份",
  "诊断",
  "examples/demo_local_narrative_project",
  "fake/local_stub",
  "fetchProjectProviderModels",
  "syncProjectProviderModels",
  "saveProjectProviderModelAssignments",
  "\"/game/input\"",
  "\"/game/start\""
]) {
  requireToken(combined, token, `v3.7/v3.8 E2E product token ${token}`);
}

for (const token of ["无需账号", "不使用云同步", "无在线市场", "不上传项目"]) {
  requireToken(combined, token, `local-only notice ${token}`);
}

forbidPattern(combined, /sk-(?!test-|fake-|redacted-)[A-Za-z0-9_-]{16,}/i, "real-looking API key");
forbidPattern(combined, /Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{12,}/i, "Authorization bearer value");
forbidPattern(combined, /<input[^>]+name=["']api_key["']/i, "plaintext api_key input");
forbidPattern(combined, /create(Account|CloudSync|OnlineMarketplace|RemoteDownload)/i, "account/cloud/marketplace/remote download entrypoint");

if (!pkg.scripts?.["check:v37-e2e-product-experience"]) {
  failures.push("package.json is missing check:v37-e2e-product-experience.");
}

if (failures.length) {
  console.error("v3.7 E2E product experience check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 E2E product experience check passed.");
