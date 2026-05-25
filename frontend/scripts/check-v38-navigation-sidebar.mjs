import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) {
    failures.push(`Missing ${label}`);
  }
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}`);
  }
}

const start = app.indexOf("function UnifiedNavigation");
const end = app.indexOf("function LocalStatusBar", start);
const nav = app.slice(start, end > start ? end : undefined);

requireToken(nav, "cnLabel: CN_COPY.nav.home", "Home entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.novel", "Novel entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.tavern", "Tavern entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.world", "World entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.provider", "Provider entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.settings", "Settings entry label");
requireToken(nav, "cnLabel: CN_COPY.nav.backup", "Backup entry label");
requireToken(nav, "const mainEntryIds = [\"home\", \"novel\", \"tavern\", \"world\"]", "main navigation order");
requireToken(nav, "const commonSettingIds = [\"provider\", \"settings\", \"backup\"]", "common settings order");
requireToken(nav, "const advancedToolIds = [\"cross-mode\", \"authoring\", \"qa\", \"diagnostics\", \"export\"]", "advanced tools order");
requireToken(nav, "data-testid=\"v37-advanced-tools-nav\"", "advanced tools foldout");
requireToken(nav, "data-default-collapsed=\"true\"", "advanced tools collapsed marker");
requireToken(nav, "尚未选择项目：主入口以弱提示显示", "no project weak prompt");
requireToken(nav, "主要入口", "main entry section title");
requireToken(nav, "常用设置", "common settings section title");
requireToken(nav, "高级工具", "advanced tools Chinese summary");
requireToken(nav, "aria-current={item.active ? \"page\" : undefined}", "active page aria current");
requireToken(nav, "aria-expanded={debugOpen}", "debug drawer aria expanded");
requireToken(nav, "需要 ENABLE_DEBUG_API", "debug disabled explanation");
requireToken(nav, "打开诊断 / Diagnostics", "diagnostics advanced entry");
requireToken(nav, "打开质量检查 / Quality Gate", "quality advanced entry");

for (const token of [
  "账号",
  "云同步",
  "在线市场",
  "marketplace",
  "cloud sync",
  "account system",
  "Authorization:",
  "Bearer ",
  "api_key:",
  "transient_api_key",
  "remote download"
]) {
  forbidToken(nav, token, `navigation forbidden token: ${token}`);
}

if (nav.includes("<DisabledState")) {
  failures.push("Sidebar should not render a disabled wall.");
}
if ((nav.match(/disabled=\{/g) ?? []).length > 1) {
  failures.push("Sidebar should avoid repeated disabled controls.");
}

requireToken(pkg.scripts?.["check:v38-navigation-sidebar"] ?? "", "node scripts/check-v38-navigation-sidebar.mjs", "package script");

if (failures.length) {
  console.error("v3.8 navigation/sidebar check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 navigation/sidebar check passed.");
