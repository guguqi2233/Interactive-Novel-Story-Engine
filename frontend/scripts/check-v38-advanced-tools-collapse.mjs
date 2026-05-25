import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "..");
const app = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const styles = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
const failures = [];

function requireToken(source, token, label = token) {
  if (!source.includes(token)) failures.push(`Missing ${label}`);
}

function forbidToken(source, token, label = token) {
  if (source.includes(token)) failures.push(`Forbidden ${label}`);
}

function sourceSlice(source, startToken, endToken, fallbackLength = 60000) {
  const start = source.indexOf(startToken);
  if (start < 0) return "";
  const end = source.indexOf(endToken, start + startToken.length);
  return source.slice(start, end > start ? end : start + fallbackLength);
}

const navSlice = sourceSlice(app, "function UnifiedNavigation", "function LocalStatusBar");
const studioHomeSlice = sourceSlice(app, "function StudioHome", "function WorldHealthDashboard");
const playableHomeSlice = sourceSlice(app, "function ChinesePlayableHomePanel", "function ProjectHomeRedesignPanel");

requireToken(navSlice, "data-testid=\"v37-advanced-tools-nav\"", "advanced tools navigation foldout");
requireToken(navSlice, "data-default-collapsed=\"true\"", "advanced tools default collapsed marker");
requireToken(navSlice, "Cross-Mode", "Cross-Mode advanced entry");
requireToken(navSlice, "创作 / Mod", "Authoring / Mod advanced entry");
requireToken(navSlice, "Quality Gate", "Quality Gate advanced entry");
requireToken(navSlice, "Debug / Replay", "Debug / Replay advanced entry");
requireToken(navSlice, "Diagnostics", "Diagnostics advanced entry");
requireToken(navSlice, "Export", "Export advanced entry");
requireToken(navSlice, "Product Readiness", "Product Readiness advanced entry");
requireToken(navSlice, "StateDelta Viewer", "StateDelta Viewer advanced entry");
requireToken(navSlice, "EventLog Viewer", "EventLog Viewer advanced entry");
requireToken(navSlice, "Hidden Leak Report", "Hidden Leak Report advanced entry");
requireToken(navSlice, "className={`nav-item debug-gated ${debugOpen ? \"active\" : \"\"}`}", "Debug active only when opened");
requireToken(navSlice, "aria-expanded={debugOpen}", "Debug expanded state bound to drawer");
requireToken(navSlice, "ENABLE_DEBUG_API", "DebugGate explanation");

requireToken(studioHomeSlice, "data-testid=\"v37-home-advanced-tools\"", "Home advanced tools foldout");
requireToken(studioHomeSlice, "data-default-collapsed=\"true\"", "Home advanced tools default collapsed marker");
requireToken(studioHomeSlice, "data-testid=\"v38-home-advanced-tool-list\"", "Home advanced tools directory");
requireToken(studioHomeSlice, "StateDelta Viewer", "Home StateDelta directory entry");
requireToken(studioHomeSlice, "EventLog Viewer", "Home EventLog directory entry");
requireToken(studioHomeSlice, "Hidden Leak Report", "Home Hidden Leak directory entry");
requireToken(studioHomeSlice, "默认收纳，避免首页变成开发者仪表盘", "Chinese collapse rationale");

requireToken(app, "const [debugOpen, setDebugOpen] = useState<boolean>(false)", "Debug panel default closed");
requireToken(app, "{debugOpen && (", "Debug panel conditional rendering");
requireToken(app, "<DebugGate debugEnabled={studioStatus?.debug_api_enabled ?? false}>", "DebugGate still guards raw debug controls");
requireToken(styles, ".advanced-tools-foldout", "advanced tools foldout styles");
requireToken(styles, ".home-advanced-tools", "home advanced tools styles");
requireToken(styles, ".home-advanced-tool-list", "home advanced tool directory styles");
requireToken(pkg.scripts?.["check:v38-advanced-tools-collapse"] ?? "", "node scripts/check-v38-advanced-tools-collapse.mjs", "package script");

for (const token of [
  "TimelineReplayPanel",
  "StateDeltaViewerPanel",
  "EventLogViewerPanel",
  "<aside id=\"debug-panel\"",
  "<pre>{JSON.stringify(event.state_deltas",
  "raw_state_delta"
]) {
  forbidToken(playableHomeSlice, token, "normal playable Home debug surface");
}

if (/data-testid="v37-advanced-tools-nav"[^>]*\sopen(=|\s|>)/.test(navSlice)) {
  failures.push("Advanced tools navigation must not render open by default.");
}
if (/data-testid="v37-home-advanced-tools"[^>]*\sopen(=|\s|>)/.test(studioHomeSlice)) {
  failures.push("Home advanced tools foldout must not render open by default.");
}

if (failures.length) {
  console.error("v3.8 advanced tools collapse UX check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.8 advanced tools collapse UX check passed.");
