import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const providerUi = readFileSync(resolve(root, "src", "providerUi.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));

const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 50000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const wizard = sourceSlice(providerUi, "function ProviderSetupWizard", "function ProviderConnectivityDashboard");
const assignmentPanel = sourceSlice(providerUi, "function ProviderModelAssignmentPanel", "function ProviderCapabilityMatrixPanel");

requireToken(wizard, "data-testid=\"v38-provider-help-section\"", "provider help section");
requireToken(wizard, "这是什么？", "plain language help title");
requireToken(wizard, "模型服务是什么", "provider explanation");
requireToken(wizard, "中转站是什么", "relay explanation");
requireToken(wizard, "Base URL 是什么", "base URL explanation");
requireToken(wizard, "API Key 放在哪里", "API key location explanation");
requireToken(wizard, "模型列表是什么", "model list explanation");
requireToken(wizard, "为什么要分配模型", "model assignment explanation");
requireToken(wizard, "兼容 API 配置", "relay compatible API wording");
requireToken(wizard, "不是 API 转售服务", "no API resale statement");
requireToken(wizard, "用户自己提供合法可用的 Base URL 和 Key", "user-provided relay credentials");
requireToken(wizard, "不推荐具体服务商", "no relay vendor recommendation");

requireToken(providerUi, "const PROVIDER_MODEL_USE_CASE_HELP", "use case help map");
requireToken(assignmentPanel, "data-testid=\"v38-provider-use-case-help\"", "model assignment help section");
requireToken(assignmentPanel, "模型使用场景说明", "model assignment help title");
requireToken(assignmentPanel, "providerModelUseCaseHelp(item.value)", "per-card use case help");
requireToken(assignmentPanel, "JSON 能力 warning", "JSON capability warning copy");
requireToken(assignmentPanel, "需要 JSON / 结构化输出", "structured output warning text");
if (!assignmentPanel.includes("模型不是世界裁判") && !assignmentPanel.includes("模型不会决定世界事实")) {
  failures.push("Missing LLM boundary explanation");
}

const useCaseLabels = [
  "小说草稿",
  "小说改写",
  "Tavern 回复",
  "多 NPC 场景",
  "世界输入解析",
  "世界叙事渲染",
  "Cross-Mode 草稿",
  "记忆摘要",
  "质量检查",
  "低成本摘要"
];
for (const label of useCaseLabels) requireToken(providerUi, label, `use case label ${label}`);

const useCaseHelpTokens = [
  "章节草稿",
  "改写、润色",
  "单角色 Tavern RP 回复",
  "多 NPC 场景对话",
  "结构化意图",
  "已确认的规则结果",
  "draft/proposal",
  "本地记忆摘要",
  "确定性 Quality Gate",
  "低成本摘要"
];
for (const token of useCaseHelpTokens) requireToken(providerUi, token, `use case help ${token}`);

requireToken(styles, ".provider-help-section", "provider help section style");
requireToken(styles, ".provider-use-case-help", "provider use case help style");
requireToken(styles, ".provider-use-case-help-grid", "provider use case help grid style");
requireToken(pkg.scripts?.["check:v38-provider-model-explanation"] ?? "", "node scripts/check-v38-provider-model-explanation.mjs", "package script");

if (/\b(localStorage|sessionStorage)\.(setItem|getItem)|window\.(localStorage|sessionStorage)/.test(wizard + assignmentPanel)) {
  failures.push("Provider explanation UI must not use browser storage APIs for secrets.");
}
if (/sk-[A-Za-z0-9_-]{12,}/.test(wizard + assignmentPanel)) {
  failures.push("Provider explanation UI contains a secret-looking sk-* token.");
}
if (/(推荐(某个|具体).*(中转站|服务商)|绑定具体中转站)/.test((wizard + assignmentPanel).replace(/不推荐具体服务商/g, ""))) {
  failures.push("Provider explanation UI must not recommend a specific relay/vendor.");
}

if (failures.length) {
  console.error("v3.8 provider/model explanation UX check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 provider/model explanation UX check passed.");
