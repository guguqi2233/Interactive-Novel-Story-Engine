import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const providerStart = appSource.indexOf("function KeyboardShortcutsProvider");
const providerEnd = appSource.indexOf("function ShortcutHelpDialog", providerStart);
const providerSource = providerStart >= 0 && providerEnd > providerStart ? appSource.slice(providerStart, providerEnd) : "";

const navStart = appSource.indexOf("function UnifiedNavigation");
const navEnd = appSource.indexOf("function LocalStatusBar", navStart);
const navSource = navStart >= 0 && navEnd > navStart ? appSource.slice(navStart, navEnd) : "";

const sharedStart = appSource.indexOf("function PageHeader");
const sharedEnd = appSource.indexOf("function moduleRiskBadgeLevel", sharedStart);
const sharedSource = sharedStart >= 0 && sharedEnd > sharedStart ? appSource.slice(sharedStart, sharedEnd) : "";

if (!providerSource) failures.push("KeyboardShortcutsProvider source slice not found.");
if (!navSource) failures.push("UnifiedNavigation source slice not found.");
if (!sharedSource) failures.push("Shared UI source slice not found.");

for (const [tokens, label] of [
  [["aria-label=\"AI Narrative Studio local workspace\""], "main local workspace landmark"],
  [["aria-label=\"Local studio navigation\"", "aria-label=\"Local studio navigation / 本地工作室导航\""], "main navigation label"],
  [["aria-current={item.active ? \"page\" : undefined}"], "active nav aria-current"],
  [["aria-label={safeAriaText(`Open ${item.label}", "aria-label={safeAriaText(`打开 ${item.cnLabel ?? item.label}"], "navigation button accessible names"],
  [["aria-label={debugOpen ? \"Hide debug drawer\" : \"Show debug drawer\"}", "aria-label={debugOpen ? \"Hide Debug / Replay panel\" : \"Open Debug / Replay panel\"}"], "debug drawer button label"],
  [["aria-controls=\"debug-panel\""], "debug panel control relationship"],
  [["aria-label=\"Open keyboard shortcuts help\""], "icon-only shortcut help button label"],
  [["function safeAriaText"], "shared safe aria text redaction helper"],
  [["aria-live=\"polite\""], "polite status live region"],
  [["aria-live=\"assertive\""], "assertive error live region"],
  [["aria-disabled=\"true\""], "disabled state semantic marker"],
  [["Risk level:"], "risk badge readable text"],
  [["Validation status:"], "validation badge readable text"],
  [["Quality severity:"], "quality severity readable text"],
  [["Leak risk severity:"], "leak risk readable text"],
  [["Model capability"], "model capability readable text"],
  [["role=\"group\" aria-label=\"Filter controls\""], "filter toolbar grouping"],
  [["Status:"], "status badge readable text"]
]) {
  if (!tokens.some((token) => appSource.includes(token))) failures.push(`Missing ${label}: ${tokens.join(" | ")}`);
}

if (!/role="status"[\s\S]*aria-label="Local-only mode"/.test(sharedSource)) {
  failures.push("Local-only badge is missing a readable status label.");
}

if (!/function ValidationStatusBadge[\s\S]*role="status"[\s\S]*aria-label=/.test(sharedSource)) {
  failures.push("ValidationStatusBadge does not expose an accessible status label.");
}

if (!/function RiskBadge[\s\S]*role="status"[\s\S]*Risk level:/.test(sharedSource)) {
  failures.push("RiskBadge does not expose an accessible risk label.");
}

if (!/function ModelCapabilityBadge[\s\S]*role="status"[\s\S]*Model capability/.test(sharedSource)) {
  failures.push("ModelCapabilityBadge does not expose an accessible capability label.");
}

if (!/aria-haspopup="dialog"[\s\S]*aria-label="Open keyboard shortcuts help"/.test(providerSource)) {
  failures.push("The icon-only shortcut help launcher is missing an accessible label.");
}

if (!/aria-label=\{safeAriaText\(title\)\}/.test(sharedSource)) {
  failures.push("Shared cards/sections do not use safe accessible names for dynamic titles.");
}

if (/aria-label=[^\n]*(sk-[A-Za-z0-9_-]{8,}|Authorization\s*[:=]|transient_api_key|api_key\s*[:=]|secret_ref\s*[:=]|raw_state_delta|npc_secret|hidden_fact_text_visible)/i.test(appSource)) {
  failures.push("An aria-label appears to include a secret-like, hidden, or raw-debug token.");
}

if (!/"check:v36-a11y-semantics"/.test(pkg)) {
  failures.push("package.json is missing check:v36-a11y-semantics.");
}

if (failures.length) {
  console.error("v3.6 Accessibility Labels / Semantics check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Accessibility Labels / Semantics check passed.");
