import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}: ${token}`);
  }
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}: ${token}`);
  }
}

requireToken(app, "className=\"responsive-sidebar-foldout\"", "responsive sidebar foldout");
requireToken(app, "data-testid=\"v38-responsive-sidebar-foldout\"", "responsive sidebar test id");
requireToken(app, "<summary>导航 / 当前状态</summary>", "Chinese collapsible sidebar summary");

for (const token of [
  "body {\n  overflow-x: hidden;",
  ".app-shell {\n  display: grid;",
  "grid-template-columns: minmax(190px, 240px) minmax(360px, 1fr) minmax(44px, 320px);",
  ".app-shell.without-debug",
  ".responsive-sidebar-foldout > summary",
  "@media (max-width: 1120px)",
  ".app-shell.with-debug",
  ".debug-panel {\n    grid-column: 1 / -1;",
  ".cn-mode-entry-grid-primary {\n    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));",
  "@media (max-width: 860px)",
  ".responsive-sidebar-foldout:not([open]) > .unified-navigation",
  ".story-panel {\n    padding: 16px;",
  "@media (max-width: 560px)",
  ".provider-explainer-grid",
  ".provider-use-case-help-grid",
  ".input-row {\n    grid-template-columns: 1fr;",
  "overflow-wrap: anywhere"
]) {
  requireToken(styles, token, `responsive layout rule: ${token}`);
}

for (const forbidden of [
  "Authorization:",
  "Bearer ",
  "transient_api_key",
  "npc_knowledge",
  "raw_state_deltas"
]) {
  forbidToken(app.slice(app.indexOf("className=\"responsive-sidebar-foldout\""), app.indexOf("<section className=\"story-panel\"")), forbidden, `responsive sidebar secret/debug token: ${forbidden}`);
}

requireToken(pkg.scripts?.["check:v38-responsive-window"] ?? "", "node scripts/check-v38-responsive-window.mjs", "package script");

if (failures.length) {
  console.error("v3.8 Responsive / Window Size Polish check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 Responsive / Window Size Polish check passed.");
