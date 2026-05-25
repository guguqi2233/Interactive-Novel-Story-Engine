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

function requireAbsent(source, token, label = token) {
  if (source.includes(token)) {
    failures.push(`Forbidden ${label}`);
  }
}

const start = app.indexOf("function ChinesePlayableHomePanel");
const end = app.indexOf("function ProjectHomeRedesignPanel", start);
const home = app.slice(start, end > start ? end : undefined);

requireToken(home, "data-testid=\"v37-project-entry-panel\"", "project entry panel");
requireToken(home, "data-testid=\"v38-project-lifecycle-summary\"", "project lifecycle summary");
requireToken(home, "项目状态", "project status summary");
requireToken(home, "安全路径摘要", "safe path summary");
requireToken(home, "项目健康", "project health summary");
requireToken(home, "加载失败恢复建议", "project load recovery summary");
requireToken(home, "打开项目", "open project CTA");
requireToken(home, "创建项目", "create project CTA");
requireToken(home, "最近项目", "recent projects section");
requireToken(home, "体验 Demo 项目", "demo project entry");
requireToken(home, "examples/demo_local_narrative_project", "demo project path");
requireToken(home, "<SafePathSummary value={project.path_redacted}", "recent project safe path renderer");
requireToken(home, "不显示敏感完整路径", "no full sensitive path copy");
requireToken(home, "用户明确展开", "explicit expand copy");
requireToken(home, "项目引用需要复核", "project load failure recovery");
requireToken(home, "路径失效", "missing recent project status");
requireToken(home, "路径需复核", "unsafe path status");
requireToken(home, "不读取任意文件、不上传路径", "local-only project health copy");
requireToken(home, "不显示 raw sensitive path", "safe project load error copy");

for (const token of [
  "project.path}",
  "project.path,",
  "project.path)",
  "full_path",
  "raw_path",
  "process.env",
  "Authorization:",
  "Bearer ",
  "transient_api_key",
  "localStorage.setItem(\"api"
]) {
  requireAbsent(home, token, `project lifecycle forbidden token: ${token}`);
}

if (/sk-(?!test|fake|example|redacted)[A-Za-z0-9_-]{12,}/.test(home)) {
  failures.push("Project lifecycle Home slice appears to contain a non-fixture key-like token.");
}

requireToken(pkg.scripts?.["check:v38-project-lifecycle-ux"] ?? "", "node scripts/check-v38-project-lifecycle-ux.mjs", "package script");

if (failures.length) {
  console.error("v3.8 project lifecycle UX check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 project lifecycle UX check passed.");
