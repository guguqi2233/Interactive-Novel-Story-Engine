import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const api = readFileSync(resolve(root, "src", "api.ts"), "utf8");
const novelUi = readFileSync(resolve(root, "src", "novelUi.tsx"), "utf8");
const main = readFileSync(resolve(root, "..", "backend", "app", "main.py"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label) {
  if (!source.includes(token)) failures.push(`Missing ${label}: ${token}`);
}

function sliceBetween(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + 26000);
}

const novelSlice = sliceBetween(app, "<h3>写小说 / Novel Studio</h3>", "<h3>Tavern Studio UI Pro</h3>");

for (const token of [
  "写小说 / Novel Studio",
  "创建稿件",
  "开始写作",
  "章节编辑器",
  "保存草稿",
  "LLM 生成草稿",
  "LLM 改写",
  "LLM 摘要",
  "配置模型服务",
  "当前模型",
  "从 World 导入章节草稿",
  "导出 Markdown",
  "导出 TXT",
  "运行 Novel Quality",
  "Novel UI 不直接修改 GameState"
]) {
  requireToken(`${novelSlice}\n${novelUi}`, token, `Novel Chinese workflow copy ${token}`);
}

requireToken(app, "data-testid=\"v37-novel-cn-llm-actions\"", "Novel LLM action test id");
requireToken(app, "generateNovelLlmDraft(selectedProjectId", "Novel LLM frontend API call");
requireToken(api, "export async function generateNovelLlmDraft", "Novel LLM API client");
requireToken(api, "/novel/llm/generate", "Novel LLM API path");
requireToken(main, "@app.post(\"/projects/{project_id}/novel/llm/generate\")", "Novel LLM backend endpoint");
requireToken(main, "NovelDraftGenerationService", "Novel generation service");
requireToken(main, "ProviderRoutingUseCase.NOVEL_DRAFT", "Novel draft ProviderGateway use case");
requireToken(main, "ProviderRoutingUseCase.NOVEL_REWRITE", "Novel rewrite ProviderGateway use case");
requireToken(main, "FakeLLMProvider(json_responses", "fake provider generation path");
requireToken(api, "export async function runNovelQuality", "Novel Quality API client");
requireToken(novelUi, "onRun && <button type=\"button\" onClick={onRun}>运行 Novel Quality</button>", "Novel Quality run button");

for (const forbidden of ["api_key", "transient_api_key", "Authorization", "raw provider response", "raw_state_delta"]) {
  if (novelSlice.includes(forbidden)) failures.push(`Novel normal UI contains forbidden token: ${forbidden}`);
}

if (/setGameState|applyStateDelta|submitPlayerInput/.test(novelSlice)) {
  failures.push("Novel Chinese workflow must not directly mutate GameState or submit world actions.");
}

if (!pkg.scripts?.["check:v37-novel-cn-workflow"]) {
  failures.push("package.json is missing check:v37-novel-cn-workflow.");
}

if (failures.length) {
  console.error("v3.7 Novel Chinese workflow check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.7 Novel Chinese workflow check passed.");
