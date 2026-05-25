import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const worldUi = readFileSync(resolve(root, "src", "worldUi.tsx"), "utf8");
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

function sliceBetween(source, startToken, endToken) {
  const start = source.indexOf(startToken);
  const end = source.indexOf(endToken, start + startToken.length);
  if (start < 0) {
    failures.push(`Missing slice start: ${startToken}`);
    return "";
  }
  return source.slice(start, end > start ? end : undefined);
}

const navSlice = sliceBetween(app, "function UnifiedNavigation", "function LocalStatusBar");
const homeSlice = sliceBetween(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");
const debugPanelSlice = sliceBetween(app, "{debugOpen && (", "</aside>");

requireToken(navSlice, "data-testid=\"v37-advanced-tools-nav\"", "advanced tools nav");
requireToken(navSlice, "data-default-collapsed=\"true\"", "advanced tools default collapsed marker");
requireToken(navSlice, "质量检查 / Quality Gate", "QA entry in advanced tools");
requireToken(navSlice, "调试 / 回放", "Debug/Replay entry in advanced tools");
requireToken(navSlice, "诊断 / Diagnostics", "Diagnostics entry in advanced tools");
requireToken(navSlice, "首页只显示简短质量状态", "Home concise quality status copy");
requireToken(navSlice, "高级 ·", "Debug advanced badge");
requireToken(navSlice, "需要 ENABLE_DEBUG_API", "Debug disabled Chinese ENABLE_DEBUG_API copy");
requireToken(navSlice, "aria-expanded={debugOpen}", "Debug drawer expansion state");
requireToken(app, "const [debugOpen, setDebugOpen] = useState<boolean>(false)", "Debug drawer default closed");
requireToken(app, "<DebugGate debugEnabled={studioStatus?.debug_api_enabled ?? false}>", "StateDelta viewer DebugGate");
requireToken(app, "<StateDeltaViewerPanel events={timeline} />", "StateDelta viewer inside gated panel");
requireToken(app, "<EventLogViewerPanel", "EventLog viewer exists");
requireToken(app, "<TimelineReplayPanel", "Timeline replay exists");
requireToken(app, "raw state_deltas remain debug-gated", "QA workflow boundary copy");
requireToken(app, "普通视图只使用 visible_state", "World normal UI safe summary copy");
requireToken(worldUi, "Raw state_deltas require DebugGate", "world UI raw delta gate copy");
requireToken(worldUi, "Hidden events are excluded from normal view", "world UI hidden event normal exclusion");
requireToken(worldUi, "DebugGate", "DebugGate component");

for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "<pre>{JSON.stringify(event.state_deltas",
  "raw_state_delta"
]) {
  forbidToken(homeSlice, token, `normal Home debug surface: ${token}`);
}

if (!debugPanelSlice.includes("<DebugGate")) {
  failures.push("Debug panel must include DebugGate before raw/debug-sensitive viewers.");
}

requireToken(pkg.scripts?.["check:v38-qa-debug-access"] ?? "", "node scripts/check-v38-qa-debug-access.mjs", "package script");

if (failures.length) {
  console.error("v3.8 QA/Debug access check failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("v3.8 QA/Debug access check passed.");
