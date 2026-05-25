import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const repoRoot = resolve(root, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const demoRoot = resolve(repoRoot, "examples", "demo_local_narrative_project");

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}`);
}

function requireAnyToken(source, tokens, label) {
  if (!tokens.some((token) => source.includes(token))) failures.push(`Missing ${label}`);
}

function walkFiles(dir) {
  const result = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) result.push(...walkFiles(fullPath));
    else result.push(fullPath);
  }
  return result;
}

const homeStart = app.indexOf("function ChinesePlayableHomePanel");
const homeEnd = app.indexOf("function ProjectHomeRedesignPanel", homeStart);
const home = app.slice(homeStart, homeEnd > homeStart ? homeEnd : undefined);

requireToken(home + app, "data-testid=\"v37-demo-project-entry\"", "Demo entry card");
requireAnyToken(home + app, ["data-testid=\"v38-demo-experience-summary\"", "DemoProjectCard", "cn-demo-project-card"], "Demo experience summary");
requireToken(home, "体验 Demo 项目", "Demo CTA");
requireToken(home, "examples/demo_local_narrative_project", "Demo path");
requireToken(home + app, "无需 API Key", "No API key copy");
requireToken(home + app, "fake/local_stub", "fake/local_stub provider copy");
requireAnyToken(home + app, ["可体验写小说", "试写小说"], "Novel demo copy");
requireAnyToken(home + app, ["可体验角色 RP", "试角色 RP"], "Tavern demo copy");
requireAnyToken(home + app, ["可体验大世界游玩", "试大世界游玩"], "World demo copy");
requireAnyToken(home + app, ["不覆盖用户项目", "不自动覆盖用户项目"], "No overwrite copy");
requireAnyToken(home + app, ["不调用真实 provider", "不需要真实 provider", "不调用真实 Provider"], "No real provider copy");
requireAnyToken(home + app, ["不上传", "不会上传"], "No upload copy");
requireAnyToken(home + app, ["data-testid=\"cn-open-demo-project\"", "testId=\"cn-open-demo-project\"", "primaryTestId=\"cn-open-demo-project\""], "Open demo button");
requireAnyToken(home + app, ["data-testid=\"cn-demo-try-novel\"", "cn-demo-try-novel"], "Try Novel button");
requireAnyToken(home + app, ["data-testid=\"cn-demo-try-tavern\"", "cn-demo-try-tavern"], "Try Tavern button");
requireAnyToken(home + app, ["data-testid=\"cn-demo-try-world\"", "cn-demo-try-world"], "Try World button");

if (!statSync(demoRoot, { throwIfNoEntry: false })?.isDirectory()) {
  failures.push("Demo project directory is missing.");
} else {
  const files = walkFiles(demoRoot);
  const joined = files.map((file) => `${file}\n${readFileSync(file, "utf8")}`).join("\n");
  requireToken(joined, "provider_type: local_stub", "Demo local_stub provider profile");
  requireToken(joined, "allow_mature_content: false", "Demo mature disabled");
  requireToken(joined, "contains_secrets", "Demo diagnostics secret marker");
  requireToken(joined, "contains_secrets\": false", "Demo diagnostics secret exclusion");
  requireToken(joined, "mature_private_included\": false", "Demo diagnostics mature/private exclusion");
  requireToken(joined, "No real provider credentials are included.", "Demo README no real credentials");
  requireToken(joined, "The demo does not call a real provider.", "Demo README no real provider");
  requireToken(joined, "The demo does not upload data.", "Demo README no upload");

  const relativeFiles = files.map((file) => file.slice(demoRoot.length + 1).replace(/\\/g, "/"));
  if (relativeFiles.some((file) => file === ".env" || file.endsWith("/.env"))) {
    failures.push("Demo project must not include a .env file.");
  }

  for (const forbidden of [
    "OPENAI_API_KEY=",
    "Authorization:",
    "Bearer ",
    "transient_api_key",
    "api_key:",
    "secret_key:",
    "private_key:",
    "node_modules",
    "frontend/dist",
    ".sqlite",
    ".db"
  ]) {
    if (joined.includes(forbidden)) failures.push(`Demo project must not contain forbidden token: ${forbidden}`);
  }
  if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(joined)) {
    failures.push("Demo project appears to contain a non-fixture key-like token.");
  }
}

requireToken(pkg.scripts?.["check:v38-demo-project-experience"] ?? "", "node scripts/check-v38-demo-project-experience.mjs", "package script");

if (failures.length) {
  console.error("v3.8 demo project experience check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 demo project experience check passed.");
