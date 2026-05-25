import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const appSource = readFileSync(resolve(root, "src", "App.tsx"), "utf8");
const cssSource = readFileSync(resolve(root, "src", "styles.css"), "utf8");
const pkg = readFileSync(resolve(root, "package.json"), "utf8");
const failures = [];

const providerStart = appSource.indexOf("function KeyboardShortcutsProvider");
const providerEnd = appSource.indexOf("function StudioHome", providerStart);
const providerSource = providerStart >= 0 && providerEnd > providerStart ? appSource.slice(providerStart, providerEnd) : "";
const effectStart = appSource.indexOf("function handleShortcutKeyDown");
const effectEnd = appSource.indexOf("const knownFacts", effectStart);
const effectSource = effectStart >= 0 && effectEnd > effectStart ? appSource.slice(effectStart, effectEnd) : "";

if (!providerSource) failures.push("KeyboardShortcutsProvider source slice not found.");
if (!effectSource) failures.push("handleShortcutKeyDown source slice not found.");

for (const [tokens, label] of [
  ["data-v36-keyboard-shortcuts", "v3.6 marker"],
  ["KeyboardShortcutsProvider", "provider component"],
  ["ShortcutHelpDialog", "shortcut help UI"],
  ["KEYBOARD_SHORTCUTS_PREF_KEY", "local preference key"],
  ["KEYBOARD_SHORTCUTS", "shortcut list"],
  ["Ctrl/Cmd+K", "global search shortcut"],
  ["Ctrl/Cmd+S", "safe save shortcut"],
  ["Esc", "escape shortcut"],
  ["g then n", "Novel navigation shortcut"],
  ["g then t", "Tavern navigation shortcut"],
  ["g then w", "World navigation shortcut"],
  ["g then a", "Authoring navigation shortcut"],
  ["g then q", "QA/debug navigation shortcut"],
  ["isEditableShortcutTarget", "editable target guard"],
  ["focusFirstSafeSearchField", "safe search focus helper"],
  ["SHORTCUT_DANGEROUS_ACTION_BLOCKLIST", "dangerous action blocklist"],
  [["Safe Apply still requires validation, dry-run, and explicit confirm", "Safe Apply 仍需要 validation、dry-run 和明确确认"], "safe apply boundary wording"],
  [["Debug views remain gated by ENABLE_DEBUG_API", "调试视图仍受 ENABLE_DEBUG_API"], "debug gate boundary wording"],
  [["Input fields ignore navigation chords", "输入框会忽略导航组合键"], "input/IME guard wording"],
  [["Enable safe keyboard shortcuts", "在此设备启用键盘快捷键"], "settings toggle"],
  [["View Keyboard Shortcuts", "键盘快捷键帮助"], "settings help action"]
]) {
  const tokenList = Array.isArray(tokens) ? tokens : [tokens];
  if (!tokenList.some((token) => appSource.includes(token))) failures.push(`Missing ${label}: ${tokenList.join(" | ")}`);
}

for (const riskyToken of [
  "handleCreateBackup()",
  "handleRestoreDryRun(",
  "handleApplyMigration(",
  "handleDeleteSave(",
  "handleCreateDiagnosticsBundle(",
  "handleCreateTavernExport(",
  "handleModuleQualityGate("
]) {
  if (effectSource.includes(riskyToken)) {
    failures.push(`Shortcut handler directly references dangerous or confirm-gated action: ${riskyToken}`);
  }
}

if (!/if \(editableTarget\)\s*\{\s*return;\s*\}/m.test(effectSource)) {
  failures.push("Shortcut handler does not clearly return for editable targets before navigation chords.");
}

if (/SafeJSON|<pre>|sk-[A-Za-z0-9_-]{12,}|Authorization\s*[:=]|transient_api_key\s*[:=]/i.test(providerSource)) {
  failures.push("Shortcut help appears to render raw JSON, secrets, auth headers, or transient key data.");
}

if (!cssSource.includes(".shortcut-help-dialog") || !cssSource.includes(".shortcut-help-launcher")) {
  failures.push("Shortcut help CSS is missing.");
}

if (!/"check:v36-keyboard-shortcuts"/.test(pkg)) {
  failures.push("package.json is missing check:v36-keyboard-shortcuts.");
}

if (failures.length) {
  console.error("v3.6 Keyboard Shortcuts Foundation check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log("v3.6 Keyboard Shortcuts Foundation check passed.");
